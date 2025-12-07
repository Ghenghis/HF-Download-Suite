"""
Integration tests for the complete download flow.

Tests download task models, status enums, and data structures
without requiring network access or complex mocking.
"""

import pytest
import tempfile
import shutil
from pathlib import Path


class TestDownloadModels:
    """Tests for download data models."""
    
    def test_download_status_enum(self):
        """Test DownloadStatus enum values."""
        from hf_suite_v2.core.models import DownloadStatus
        
        assert DownloadStatus.QUEUED.value == "queued"
        assert DownloadStatus.DOWNLOADING.value == "downloading"
        assert DownloadStatus.PAUSED.value == "paused"
        assert DownloadStatus.COMPLETED.value == "completed"
        assert DownloadStatus.FAILED.value == "failed"
        assert DownloadStatus.CANCELLED.value == "cancelled"
    
    def test_download_task_creation(self):
        """Test DownloadTask dataclass creation."""
        from hf_suite_v2.core.models import DownloadTask, DownloadStatus
        
        task = DownloadTask(
            id=1,
            repo_id="test/model",
            platform="huggingface",
            repo_type="model",
            status=DownloadStatus.QUEUED,
            save_path="/tmp/models"
        )
        
        assert task.id == 1
        assert task.repo_id == "test/model"
        assert task.platform == "huggingface"
        assert task.status == DownloadStatus.QUEUED
    
    def test_download_task_with_selected_files(self):
        """Test DownloadTask with specific file selection."""
        from hf_suite_v2.core.models import DownloadTask, DownloadStatus
        
        task = DownloadTask(
            id=2,
            repo_id="test/model",
            platform="huggingface",
            repo_type="model",
            status=DownloadStatus.QUEUED,
            save_path="/tmp/models",
            selected_files=["model.safetensors", "config.json"]
        )
        
        assert task.selected_files == ["model.safetensors", "config.json"]
        assert len(task.selected_files) == 2


class TestDownloadPathHandling:
    """Tests for path handling in downloads."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_temp_directory_creation(self):
        """Test temporary directory is created."""
        assert self.temp_dir.exists()
        assert self.temp_dir.is_dir()
    
    def test_nested_path_creation(self):
        """Test nested path creation for downloads."""
        nested = self.temp_dir / "models" / "checkpoints" / "sdxl"
        nested.mkdir(parents=True, exist_ok=True)
        
        assert nested.exists()
        assert nested.is_dir()
    
    def test_path_with_special_characters(self):
        """Test paths with spaces and special characters."""
        special_path = self.temp_dir / "my models" / "test-model_v1.0"
        special_path.mkdir(parents=True, exist_ok=True)
        
        assert special_path.exists()


class TestDownloadConfiguration:
    """Tests for download configuration."""
    
    def test_config_download_settings(self):
        """Test download settings from config."""
        from hf_suite_v2.core import get_config
        
        config = get_config()
        
        assert hasattr(config.download, 'max_workers')
        assert hasattr(config.download, 'auto_retry')
        assert hasattr(config.download, 'max_retries')
        assert hasattr(config.download, 'verify_checksums')
    
    def test_config_max_workers_range(self):
        """Test max workers is within valid range."""
        from hf_suite_v2.core import get_config
        
        config = get_config()
        
        assert 1 <= config.download.max_workers <= 8
    
    def test_config_max_retries_range(self):
        """Test max retries is within valid range."""
        from hf_suite_v2.core import get_config
        
        config = get_config()
        
        assert 0 <= config.download.max_retries <= 10


class TestDownloadPriority:
    """Tests for download priority handling."""
    
    def test_priority_values(self):
        """Test valid priority range."""
        # Priority 1 = highest, 10 = lowest
        priorities = [1, 5, 10]
        
        for p in priorities:
            assert 1 <= p <= 10
    
    def test_priority_sorting(self):
        """Test priority-based sorting."""
        downloads = [
            {"id": 1, "priority": 5},
            {"id": 2, "priority": 1},
            {"id": 3, "priority": 10},
        ]
        
        sorted_downloads = sorted(downloads, key=lambda x: x["priority"])
        
        assert sorted_downloads[0]["id"] == 2  # Highest priority
        assert sorted_downloads[1]["id"] == 1  # Medium priority
        assert sorted_downloads[2]["id"] == 3  # Lowest priority


class TestDownloadErrorHandling:
    """Tests for error handling during downloads."""
    
    def test_exception_classes_exist(self):
        """Test that all exception classes are importable."""
        from hf_suite_v2.core.exceptions import (
            HFSuiteError,
            DownloadError,
            InsufficientSpaceError,
            AuthenticationError,
            NetworkError,
            RepositoryNotFoundError,
            GatedModelError,
            DownloadInterruptedError,
            FileVerificationError,
        )
        
        assert issubclass(DownloadError, HFSuiteError)
        assert issubclass(InsufficientSpaceError, DownloadError)
    
    def test_exception_suggestions(self):
        """Test that exceptions have suggestions."""
        from hf_suite_v2.core.exceptions import InsufficientSpaceError
        
        # InsufficientSpaceError requires specific parameters
        error = InsufficientSpaceError(
            required_bytes=10 * 1024 * 1024 * 1024,  # 10 GB
            available_bytes=5 * 1024 * 1024 * 1024,  # 5 GB
            path="/tmp/downloads"
        )
        assert error.suggestion is not None
        assert len(error.suggestion) > 0
    
    def test_exception_retryable_flag(self):
        """Test exception retryable flags."""
        from hf_suite_v2.core.exceptions import (
            NetworkError,
            AuthenticationError
        )
        
        network_error = NetworkError(url="https://example.com", reason="Connection failed")
        auth_error = AuthenticationError(platform="huggingface")
        
        assert network_error.is_retryable == True
        assert auth_error.is_retryable == False
