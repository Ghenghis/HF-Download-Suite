"""
Download queue manager with worker pool.
"""

import logging
import threading
import time
from queue import PriorityQueue
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, field

from PyQt6.QtCore import QObject, pyqtSignal

from ..models import DownloadTask, DownloadStatus, ProgressInfo
from ..database import get_db
from ..events import EventBus, Events
from ..config import get_config
from .worker import DownloadWorker

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PrioritizedTask:
    """Wrapper for priority queue ordering."""
    priority: int
    task: DownloadTask = field(compare=False)


class DownloadManager(QObject):
    """
    Central download queue manager with worker pool.
    
    Manages multiple concurrent downloads with pause/resume,
    priority ordering, and progress tracking.
    
    Signals:
        task_started: Emitted when a download starts (task_id)
        task_progress: Emitted with progress updates (ProgressInfo)
        task_completed: Emitted when download completes (task_id, path)
        task_failed: Emitted on failure (task_id, error_message)
        task_cancelled: Emitted when cancelled (task_id)
        queue_changed: Emitted when queue contents change
    """
    
    # Qt signals for UI updates
    task_started = pyqtSignal(int)
    task_progress = pyqtSignal(object)  # ProgressInfo
    task_completed = pyqtSignal(int, str)
    task_failed = pyqtSignal(int, str)
    task_cancelled = pyqtSignal(int)
    queue_changed = pyqtSignal()
    
    def __init__(self, max_workers: int = None):
        super().__init__()
        
        config = get_config()
        self.max_workers = max_workers or config.download.max_workers
        self.bandwidth_limit = config.download.bandwidth_limit
        
        self._queue: PriorityQueue[PrioritizedTask] = PriorityQueue()
        self._workers: Dict[int, DownloadWorker] = {}  # task_id -> worker
        self._active_tasks: Dict[int, DownloadTask] = {}
        self._paused_tasks: Dict[int, DownloadTask] = {}
        
        self._lock = threading.Lock()
        self._running = False
        self._manager_thread: Optional[threading.Thread] = None
        
        self.db = get_db()
        self.event_bus = EventBus()
        
        # Restore pending downloads from database
        self._restore_pending()
    
    def _restore_pending(self) -> None:
        """Restore pending downloads from database on startup."""
        try:
            pending = self.db.get_pending_downloads()
            for download in pending:
                task = DownloadTask(
                    id=download.id,
                    repo_id=download.repo_id,
                    platform=download.platform,
                    repo_type=download.repo_type,
                    status=DownloadStatus.QUEUED,
                    save_path=download.save_path,
                    priority=download.priority,
                    total_bytes=download.total_bytes,
                    downloaded_bytes=download.downloaded_bytes,
                )
                self._queue.put(PrioritizedTask(task.priority, task))
            
            if pending:
                logger.info(f"Restored {len(pending)} pending downloads")
        except Exception as e:
            logger.error(f"Failed to restore pending downloads: {e}")
    
    def start(self) -> None:
        """Start the download manager."""
        if self._running:
            return
        
        self._running = True
        self._manager_thread = threading.Thread(target=self._run_manager, daemon=True)
        self._manager_thread.start()
        logger.info(f"Download manager started with {self.max_workers} workers")
    
    def stop(self) -> None:
        """Stop the download manager and all workers."""
        self._running = False
        
        # Cancel all active downloads
        with self._lock:
            for task_id, worker in list(self._workers.items()):
                worker.cancel()
            self._workers.clear()
        
        if self._manager_thread and self._manager_thread.is_alive():
            self._manager_thread.join(timeout=5)
        
        logger.info("Download manager stopped")
    
    def _run_manager(self) -> None:
        """Main manager loop that assigns tasks to workers."""
        while self._running:
            try:
                # Check if we can start more downloads
                with self._lock:
                    active_count = len(self._workers)
                
                if active_count < self.max_workers and not self._queue.empty():
                    try:
                        prioritized = self._queue.get_nowait()
                        task = prioritized.task
                        self._start_download(task)
                    except Exception:
                        pass
                
                # Clean up completed workers
                self._cleanup_workers()
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Manager loop error: {e}")
    
    def _cleanup_workers(self) -> None:
        """Remove finished workers."""
        with self._lock:
            finished = [
                task_id for task_id, worker in self._workers.items()
                if not worker.is_running()
            ]
            for task_id in finished:
                del self._workers[task_id]
                if task_id in self._active_tasks:
                    del self._active_tasks[task_id]
    
    def add(
        self,
        repo_id: str,
        save_path: str,
        platform: str = "huggingface",
        repo_type: str = "model",
        priority: int = 5,
        selected_files: List[str] = None,
        profile_id: int = None,
    ) -> int:
        """
        Add a download to the queue.
        
        Args:
            repo_id: Repository ID (e.g., "username/model-name")
            save_path: Local path to save files
            platform: Platform name ("huggingface", "modelscope")
            repo_type: Type ("model", "dataset")
            priority: Priority 1-10 (lower = higher priority)
            selected_files: Specific files to download, None = all
            profile_id: Optional profile ID to use
        
        Returns:
            Task ID
        """
        # Save to database
        task_id = self.db.add_download({
            "repo_id": repo_id,
            "platform": platform,
            "repo_type": repo_type,
            "status": "queued",
            "save_path": save_path,
            "priority": priority,
            "profile_id": profile_id,
        })
        
        # Create task object
        task = DownloadTask(
            id=task_id,
            repo_id=repo_id,
            platform=platform,
            repo_type=repo_type,
            status=DownloadStatus.QUEUED,
            save_path=save_path,
            selected_files=selected_files,
            priority=priority,
            profile_id=profile_id,
        )
        
        # Add to queue
        self._queue.put(PrioritizedTask(priority, task))
        
        # Emit events
        self.queue_changed.emit()
        self.event_bus.emit(Events.DOWNLOAD_QUEUED, task_id=task_id, repo_id=repo_id)
        
        logger.info(f"Added download to queue: {repo_id} (ID: {task_id})")
        return task_id
    
    def _start_download(self, task: DownloadTask) -> None:
        """Start a download worker for a task."""
        with self._lock:
            if task.id in self._workers:
                return
            
            worker = DownloadWorker(task)
            
            # Connect worker signals
            worker.progress.connect(self._on_worker_progress)
            worker.completed.connect(self._on_worker_completed)
            worker.failed.connect(self._on_worker_failed)
            
            self._workers[task.id] = worker
            self._active_tasks[task.id] = task
        
        # Update database
        self.db.update_download(task.id, status="downloading")
        
        # Start worker
        worker.start()
        
        # Emit events
        self.task_started.emit(task.id)
        self.event_bus.emit(Events.DOWNLOAD_STARTED, task_id=task.id)
        
        logger.info(f"Started download: {task.repo_id}")
    
    def pause(self, task_id: int) -> bool:
        """Pause an active download."""
        with self._lock:
            if task_id not in self._workers:
                return False
            
            worker = self._workers[task_id]
            worker.pause()
            
            task = self._active_tasks.get(task_id)
            if task:
                task.status = DownloadStatus.PAUSED
                self._paused_tasks[task_id] = task
        
        self.db.update_download(task_id, status="paused")
        self.event_bus.emit(Events.DOWNLOAD_PAUSED, task_id=task_id)
        
        logger.info(f"Paused download: {task_id}")
        return True
    
    def resume(self, task_id: int) -> bool:
        """Resume a paused download."""
        with self._lock:
            if task_id not in self._paused_tasks:
                return False
            
            task = self._paused_tasks.pop(task_id)
            task.status = DownloadStatus.QUEUED
        
        # Re-add to queue
        self._queue.put(PrioritizedTask(task.priority, task))
        self.db.update_download(task_id, status="queued")
        
        self.queue_changed.emit()
        self.event_bus.emit(Events.DOWNLOAD_RESUMED, task_id=task_id)
        
        logger.info(f"Resumed download: {task_id}")
        return True
    
    def cancel(self, task_id: int) -> bool:
        """Cancel a download."""
        with self._lock:
            # Cancel active download
            if task_id in self._workers:
                self._workers[task_id].cancel()
                del self._workers[task_id]
            
            # Remove from active tasks
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
            
            # Remove from paused
            if task_id in self._paused_tasks:
                del self._paused_tasks[task_id]
        
        # Update database
        self.db.update_download(task_id, status="cancelled")
        
        # Emit events
        self.task_cancelled.emit(task_id)
        self.queue_changed.emit()
        self.event_bus.emit(Events.DOWNLOAD_CANCELLED, task_id=task_id)
        
        logger.info(f"Cancelled download: {task_id}")
        return True
    
    def set_priority(self, task_id: int, priority: int) -> bool:
        """Change download priority."""
        priority = max(1, min(10, priority))
        self.db.update_download(task_id, priority=priority)
        return True
    
    def pause_all(self) -> int:
        """Pause all active downloads.
        
        Returns:
            Number of downloads paused
        """
        paused_count = 0
        with self._lock:
            task_ids = list(self._workers.keys())
        
        for task_id in task_ids:
            if self.pause(task_id):
                paused_count += 1
        
        logger.info(f"Paused {paused_count} downloads")
        return paused_count
    
    def resume_all(self) -> int:
        """Resume all paused downloads.
        
        Returns:
            Number of downloads resumed
        """
        resumed_count = 0
        with self._lock:
            task_ids = list(self._paused_tasks.keys())
        
        for task_id in task_ids:
            if self.resume(task_id):
                resumed_count += 1
        
        logger.info(f"Resumed {resumed_count} downloads")
        return resumed_count
    
    def get_active_downloads(self) -> List[DownloadTask]:
        """Get list of active downloads."""
        with self._lock:
            return list(self._active_tasks.values())
    
    def get_queue_size(self) -> int:
        """Get number of items in queue."""
        return self._queue.qsize()
    
    def get_status(self) -> Dict:
        """Get overall manager status."""
        with self._lock:
            return {
                "running": self._running,
                "active_count": len(self._workers),
                "paused_count": len(self._paused_tasks),
                "queue_size": self._queue.qsize(),
                "max_workers": self.max_workers,
            }
    
    def _on_worker_progress(self, progress: ProgressInfo) -> None:
        """Handle worker progress update."""
        self.task_progress.emit(progress)
        
        # Update database periodically (not every update)
        self.db.update_download(
            progress.task_id,
            downloaded_bytes=progress.downloaded_bytes,
            total_bytes=progress.total_bytes,
            speed_bps=progress.speed_bps,
        )
    
    def _on_worker_completed(self, task_id: int, save_path: str) -> None:
        """Handle worker completion."""
        with self._lock:
            if task_id in self._active_tasks:
                task = self._active_tasks.pop(task_id)
            else:
                task = None
        
        # Update database
        self.db.update_download(task_id, status="completed")
        
        # Add to history
        if task:
            self.db.add_to_history({
                "repo_id": task.repo_id,
                "platform": task.platform,
                "repo_type": task.repo_type,
                "save_path": save_path,
                "total_bytes": task.total_bytes,
            })
        
        # Emit events
        self.task_completed.emit(task_id, save_path)
        self.queue_changed.emit()
        self.event_bus.emit(Events.DOWNLOAD_COMPLETED, task_id=task_id, path=save_path)
        
        logger.info(f"Download completed: {task_id}")
    
    def _on_worker_failed(self, task_id: int, error: str) -> None:
        """Handle worker failure."""
        with self._lock:
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
        
        # Update database
        self.db.update_download(task_id, status="failed", error_message=error)
        
        # Emit events
        self.task_failed.emit(task_id, error)
        self.queue_changed.emit()
        self.event_bus.emit(Events.DOWNLOAD_FAILED, task_id=task_id, error=error)
        
        logger.error(f"Download failed: {task_id} - {error}")


# Global instance
_manager_instance: Optional[DownloadManager] = None


def get_download_manager() -> DownloadManager:
    """Get the global download manager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = DownloadManager()
    return _manager_instance
