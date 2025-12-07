"""
Download worker thread for individual downloads.

Supports:
- Pause/Resume: Downloads can be paused and resumed
- Resume from interruption: Partially downloaded files are resumed
- Per-file selection: Download only selected files from a repo
- Progress tracking: Speed, ETA, and progress updates
"""

import logging
import os
import time
import threading
import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict

from PyQt6.QtCore import QThread, pyqtSignal

from ..models import DownloadTask, ProgressInfo, DownloadStatus
from ..config import get_config
from ..constants import APP_DATA_DIR
from ..exceptions import InsufficientSpaceError, AuthenticationError, GatedModelError

logger = logging.getLogger(__name__)

# Resume state file location
RESUME_STATE_DIR = APP_DATA_DIR / "resume_states"
RESUME_STATE_DIR.mkdir(parents=True, exist_ok=True)


class DownloadWorker(QThread):
    """
    Worker thread for downloading a single repository.
    
    Supports pause/resume and emits progress signals.
    
    Signals:
        progress: Emitted with ProgressInfo updates
        completed: Emitted on success (task_id, save_path)
        failed: Emitted on failure (task_id, error_message)
    """
    
    progress = pyqtSignal(object)  # ProgressInfo
    completed = pyqtSignal(int, str)
    failed = pyqtSignal(int, str)
    
    def __init__(self, task: DownloadTask, resume: bool = True):
        super().__init__()
        
        self.task = task
        self.config = get_config()
        self.resume_enabled = resume
        
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._is_running = False
        
        # Progress tracking
        self._downloaded_bytes = task.downloaded_bytes
        self._total_bytes = task.total_bytes
        self._speed_samples = []
        self._last_progress_time = 0
        self._files_completed = 0
        self._files_total = 0
        self._current_file = None
        
        # Resume state
        self._resume_state_file = RESUME_STATE_DIR / f"task_{task.id}.json"
        self._resume_state = self._load_resume_state()
    
    def run(self) -> None:
        """Main worker execution."""
        self._is_running = True
        self._cancel_event.clear()
        self._pause_event.clear()
        
        # Store original environment variables for cleanup
        original_env = {
            "HF_ENDPOINT": os.environ.get("HF_ENDPOINT"),
            "HF_HUB_DISABLE_SSL_VERIFICATION": os.environ.get("HF_HUB_DISABLE_SSL_VERIFICATION"),
        }
        
        try:
            # Retry configuration
            max_retries = self.config.download.max_retries if self.config.download.auto_retry else 0
            retry_delay = self.config.download.retry_delay
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    if self.task.platform == "huggingface":
                        self._download_huggingface()
                    elif self.task.platform == "modelscope":
                        self._download_modelscope()
                    else:
                        raise ValueError(f"Unsupported platform: {self.task.platform}")
                    
                    # Success
                    save_path = os.path.join(self.task.save_path, self.task.repo_name)
                    self.completed.emit(self.task.id, save_path)
                    return  # Exit on success
                    
                except (InsufficientSpaceError, AuthenticationError, GatedModelError) as e:
                    # These errors should not be retried
                    logger.error(f"Non-retryable error: {e}")
                    self.failed.emit(self.task.id, str(e))
                    return
                    
                except KeyboardInterrupt:
                    # User cancelled
                    logger.info(f"Download cancelled: {self.task.id}")
                    return
                    
                except Exception as e:
                    last_error = e
                    
                    if self._cancel_event.is_set():
                        logger.info(f"Download cancelled: {self.task.id}")
                        return
                    
                    if attempt < max_retries:
                        # Calculate exponential backoff delay
                        backoff_delay = retry_delay * (2 ** attempt)
                        logger.warning(
                            f"Download attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {backoff_delay}s..."
                        )
                        
                        # Wait with backoff, checking for cancel
                        for _ in range(backoff_delay):
                            if self._cancel_event.is_set():
                                logger.info(f"Download cancelled during retry wait: {self.task.id}")
                                return
                            time.sleep(1)
                    else:
                        # All retries exhausted
                        error_msg = str(last_error)
                        logger.error(f"Download failed after {max_retries + 1} attempts: {error_msg}")
                        self.failed.emit(self.task.id, error_msg)
        finally:
            self._is_running = False
            # Restore original environment variables
            self._restore_environment(original_env)
    
    def _restore_environment(self, original_env: dict) -> None:
        """Restore original environment variables."""
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    
    def _download_huggingface(self) -> None:
        """Download from HuggingFace with resume support."""
        from huggingface_hub import snapshot_download, hf_hub_download, HfFolder, HfApi
        
        # Set up token if available
        token = os.environ.get("HF_TOKEN")
        if token:
            HfFolder.save_token(token)
        
        # Set up endpoint
        endpoint = self.config.get_effective_endpoint("huggingface")
        if endpoint:
            os.environ["HF_ENDPOINT"] = endpoint
            if "hf-mirror.com" in endpoint:
                os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"
        
        # Estimate download size and check disk space
        estimated_size = self._estimate_repo_size()
        self._check_disk_space(self.task.save_path, estimated_size)
        
        # Prepare download directory
        repo_dir = os.path.join(self.task.save_path, self.task.repo_name)
        os.makedirs(repo_dir, exist_ok=True)
        
        # Check if we have specific files to download
        if self.task.selected_files:
            self._download_selected_files_hf(repo_dir, token, endpoint)
        else:
            self._download_full_repo_hf(repo_dir, token, endpoint)
        
        # Clean up resume state on success
        self._cleanup_resume_state()
        
        logger.info(f"HuggingFace download completed: {repo_dir}")
    
    def _download_selected_files_hf(self, repo_dir: str, token: str, endpoint: str) -> None:
        """Download selected files with resume support."""
        from huggingface_hub import hf_hub_download
        
        files = self.task.selected_files
        self._files_total = len(files)
        
        # Get files already completed from resume state
        completed_files = set(self._resume_state.get("completed_files", []))
        
        for i, file_path in enumerate(files):
            if self._cancel_event.is_set():
                raise KeyboardInterrupt("Download cancelled")
            
            # Skip if already completed
            if file_path in completed_files:
                self._files_completed = i + 1
                logger.debug(f"Skipping already downloaded: {file_path}")
                continue
            
            # Wait if paused
            while self._pause_event.is_set():
                self._save_resume_state()
                time.sleep(0.5)
                if self._cancel_event.is_set():
                    raise KeyboardInterrupt("Download cancelled")
            
            self._current_file = file_path
            self._files_completed = i
            
            try:
                # Download with resume support
                local_path = hf_hub_download(
                    repo_id=self.task.repo_id,
                    filename=file_path,
                    repo_type=self.task.repo_type,
                    local_dir=repo_dir,
                    token=token,
                    resume_download=True,  # Enable resume
                    force_download=False,
                    endpoint=endpoint,
                )
                
                # Mark as completed
                completed_files.add(file_path)
                self._resume_state["completed_files"] = list(completed_files)
                self._save_resume_state()
                
                logger.debug(f"Downloaded: {file_path} -> {local_path}")
                
            except Exception as e:
                logger.error(f"Failed to download {file_path}: {e}")
                raise
        
        self._files_completed = self._files_total
    
    def _download_full_repo_hf(self, repo_dir: str, token: str, endpoint: str) -> None:
        """Download full repository with resume support."""
        from huggingface_hub import snapshot_download
        
        # snapshot_download already supports resume via local_dir
        result = snapshot_download(
            repo_id=self.task.repo_id,
            repo_type=self.task.repo_type,
            local_dir=repo_dir,
            token=token,
            force_download=False,  # This enables resume
            resume_download=True,
            endpoint=endpoint,
        )
        
        return result
    
    def _download_modelscope(self) -> None:
        """Download from ModelScope."""
        try:
            from modelscope.hub.snapshot_download import snapshot_download
        except ImportError:
            raise ImportError("ModelScope library not installed")
        
        # Prepare download directory
        repo_dir = os.path.join(self.task.save_path, self.task.repo_name)
        os.makedirs(repo_dir, exist_ok=True)
        
        # Download
        result = snapshot_download(
            model_id=self.task.repo_id,
            local_dir=repo_dir,
            revision="master",
        )
        
        logger.info(f"ModelScope download completed: {result}")
    
    def _check_disk_space(self, save_path: str, required_bytes: int) -> None:
        """
        Check if there's enough disk space for the download.
        
        Args:
            save_path: Directory where files will be saved
            required_bytes: Estimated bytes needed for download
            
        Raises:
            InsufficientSpaceError: If not enough space available
        """
        if required_bytes <= 0:
            return  # Skip check if size is unknown
        
        try:
            # Get disk usage for the save path
            # Ensure parent directory exists for the check
            check_path = Path(save_path)
            while not check_path.exists():
                check_path = check_path.parent
                if check_path == check_path.parent:
                    break  # Reached root
            
            disk_usage = shutil.disk_usage(str(check_path))
            available = disk_usage.free
            
            # Add 10% buffer for safety
            required_with_buffer = int(required_bytes * 1.1)
            
            if available < required_with_buffer:
                raise InsufficientSpaceError(
                    required_bytes=required_bytes,
                    available_bytes=available,
                    path=str(check_path)
                )
            
            logger.debug(
                f"Disk space check passed: need {required_bytes / 1e9:.2f} GB, "
                f"have {available / 1e9:.2f} GB"
            )
        except InsufficientSpaceError:
            raise
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
    
    def _estimate_repo_size(self) -> int:
        """
        Estimate the total size of the repository to download.
        
        Returns:
            Estimated size in bytes, or 0 if unknown
        """
        try:
            if self.task.platform == "huggingface":
                return self._estimate_hf_repo_size()
            elif self.task.platform == "modelscope":
                return self._estimate_ms_repo_size()
        except Exception as e:
            logger.warning(f"Could not estimate repo size: {e}")
        return 0
    
    def _estimate_hf_repo_size(self) -> int:
        """Estimate HuggingFace repository size."""
        from huggingface_hub import HfApi
        
        api = HfApi()
        token = os.environ.get("HF_TOKEN")
        
        try:
            # Get repo info with file details
            repo_info = api.repo_info(
                repo_id=self.task.repo_id,
                repo_type=self.task.repo_type,
                token=token,
                files_metadata=True
            )
            
            # Sum up file sizes
            total_size = 0
            selected_files = set(self.task.selected_files) if self.task.selected_files else None
            
            if hasattr(repo_info, 'siblings'):
                for sibling in repo_info.siblings:
                    if selected_files is None or sibling.rfilename in selected_files:
                        if hasattr(sibling, 'size') and sibling.size:
                            total_size += sibling.size
            
            # Update task with total bytes
            self._total_bytes = total_size
            
            logger.info(f"Estimated download size: {total_size / 1e9:.2f} GB")
            return total_size
            
        except Exception as e:
            if "401" in str(e) or "403" in str(e):
                raise AuthenticationError("huggingface", str(e))
            elif "gated" in str(e).lower():
                raise GatedModelError(self.task.repo_id)
            raise
    
    def _estimate_ms_repo_size(self) -> int:
        """Estimate ModelScope repository size."""
        # ModelScope API is less consistent, return 0 to skip check
        return 0
    
    def _update_progress(self, downloaded: int, total: int) -> None:
        """Update and emit progress."""
        now = time.time()
        
        # Calculate speed
        if self._last_progress_time > 0:
            time_delta = now - self._last_progress_time
            bytes_delta = downloaded - self._downloaded_bytes
            if time_delta > 0:
                speed = bytes_delta / time_delta
                self._speed_samples.append(speed)
                # Keep last 10 samples for averaging
                self._speed_samples = self._speed_samples[-10:]
        
        self._downloaded_bytes = downloaded
        self._total_bytes = total
        self._last_progress_time = now
        
        # Calculate average speed
        avg_speed = sum(self._speed_samples) / len(self._speed_samples) if self._speed_samples else 0
        
        # Calculate ETA
        remaining = total - downloaded
        eta = int(remaining / avg_speed) if avg_speed > 0 else None
        
        # Emit progress (throttle to every 0.5 seconds)
        if now - getattr(self, '_last_emit_time', 0) >= 0.5:
            self._last_emit_time = now
            
            progress = ProgressInfo(
                task_id=self.task.id,
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed_bps=avg_speed,
                eta_seconds=eta,
            )
            self.progress.emit(progress)
    
    def pause(self) -> None:
        """Pause the download."""
        self._pause_event.set()
        logger.debug(f"Worker paused: {self.task.id}")
    
    def resume(self) -> None:
        """Resume the download."""
        self._pause_event.clear()
        logger.debug(f"Worker resumed: {self.task.id}")
    
    def cancel(self) -> None:
        """Cancel the download."""
        self._cancel_event.set()
        self._pause_event.clear()  # Unpause to allow cancellation
        logger.debug(f"Worker cancelled: {self.task.id}")
    
    def is_running(self) -> bool:
        """Check if worker is actively running."""
        return self._is_running
    
    def is_paused(self) -> bool:
        """Check if worker is paused."""
        return self._pause_event.is_set()
    
    # Resume state management
    
    def _load_resume_state(self) -> Dict:
        """Load resume state from file."""
        if self._resume_state_file.exists():
            try:
                with open(self._resume_state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load resume state: {e}")
        return {"completed_files": [], "downloaded_bytes": 0}
    
    def _save_resume_state(self) -> None:
        """Save current state for resume."""
        try:
            self._resume_state["downloaded_bytes"] = self._downloaded_bytes
            self._resume_state["current_file"] = self._current_file
            self._resume_state["files_completed"] = self._files_completed
            
            with open(self._resume_state_file, "w") as f:
                json.dump(self._resume_state, f)
        except Exception as e:
            logger.warning(f"Failed to save resume state: {e}")
    
    def _cleanup_resume_state(self) -> None:
        """Remove resume state file on successful completion."""
        try:
            if self._resume_state_file.exists():
                self._resume_state_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup resume state: {e}")
    
    @staticmethod
    def get_resumable_downloads() -> List[int]:
        """Get list of task IDs that can be resumed."""
        resumable = []
        for state_file in RESUME_STATE_DIR.glob("task_*.json"):
            try:
                task_id = int(state_file.stem.replace("task_", ""))
                resumable.append(task_id)
            except ValueError:
                pass
        return resumable
    
    @staticmethod
    def clear_resume_state(task_id: int) -> bool:
        """Clear resume state for a task."""
        state_file = RESUME_STATE_DIR / f"task_{task_id}.json"
        if state_file.exists():
            try:
                state_file.unlink()
                return True
            except Exception:
                pass
        return False
