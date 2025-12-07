"""
Tests for Pydantic data models.
"""

import pytest
from datetime import datetime

from hf_suite_v2.core.models import (
    DownloadTask, DownloadStatus, Platform, RepoType,
    ProgressInfo, RepoInfo, HistoryEntry, Profile
)


class TestDownloadTask:
    """Tests for DownloadTask model."""
    
    def test_create_minimal(self):
        """Test creating task with minimal fields."""
        task = DownloadTask(
            repo_id="user/model",
            save_path="/path/to/save",
        )
        assert task.repo_id == "user/model"
        assert task.status == DownloadStatus.PENDING
        assert task.platform == Platform.HUGGINGFACE
        assert task.priority == 5
    
    def test_create_full(self):
        """Test creating task with all fields."""
        task = DownloadTask(
            id=1,
            repo_id="user/model",
            platform=Platform.MODELSCOPE,
            repo_type=RepoType.DATASET,
            status=DownloadStatus.DOWNLOADING,
            save_path="/path/to/save",
            selected_files=["file1.bin", "file2.bin"],
            total_bytes=1000000,
            downloaded_bytes=500000,
            priority=1,
        )
        assert task.id == 1
        assert task.platform == Platform.MODELSCOPE
        assert task.progress_percent == 50.0
    
    def test_repo_name_extraction(self):
        """Test repo_name property."""
        task = DownloadTask(repo_id="username/model-name", save_path="/tmp")
        assert task.repo_name == "model-name"
        
        task2 = DownloadTask(repo_id="simple-name", save_path="/tmp")
        assert task2.repo_name == "simple-name"
    
    def test_progress_percent_zero_total(self):
        """Test progress calculation with zero total."""
        task = DownloadTask(
            repo_id="user/model",
            save_path="/tmp",
            total_bytes=0,
            downloaded_bytes=100,
        )
        assert task.progress_percent == 0.0
    
    def test_is_active(self):
        """Test is_active property."""
        task = DownloadTask(repo_id="user/model", save_path="/tmp")
        assert not task.is_active
        
        task.status = DownloadStatus.DOWNLOADING
        assert task.is_active
        
        task.status = DownloadStatus.QUEUED
        assert task.is_active
        
        task.status = DownloadStatus.COMPLETED
        assert not task.is_active


class TestProgressInfo:
    """Tests for ProgressInfo model."""
    
    def test_speed_formatted(self):
        """Test speed formatting."""
        # Bytes per second
        progress = ProgressInfo(task_id=1, downloaded_bytes=0, total_bytes=100, speed_bps=500)
        assert "B/s" in progress.speed_formatted
        
        # Kilobytes per second
        progress.speed_bps = 5000
        assert "KB/s" in progress.speed_formatted
        
        # Megabytes per second
        progress.speed_bps = 5000000
        assert "MB/s" in progress.speed_formatted
    
    def test_eta_formatted(self):
        """Test ETA formatting."""
        progress = ProgressInfo(task_id=1, downloaded_bytes=0, total_bytes=100, speed_bps=100)
        
        # Seconds
        progress.eta_seconds = 45
        assert progress.eta_formatted == "45s"
        
        # Minutes
        progress.eta_seconds = 125
        assert "2m" in progress.eta_formatted
        
        # Hours
        progress.eta_seconds = 3700
        assert "1h" in progress.eta_formatted
        
        # Unknown
        progress.eta_seconds = None
        assert progress.eta_formatted == "Unknown"


class TestRepoInfo:
    """Tests for RepoInfo model."""
    
    def test_display_name(self):
        """Test display_name property."""
        repo = RepoInfo(
            repo_id="username/my-model",
            author="username",
            name="my-model",
        )
        assert repo.display_name == "my-model"
        
        repo.name = ""
        assert repo.display_name == "my-model"  # Falls back to repo_id split
    
    def test_default_values(self):
        """Test default values."""
        repo = RepoInfo(
            repo_id="user/model",
            author="user",
            name="model",
        )
        assert repo.platform == Platform.HUGGINGFACE
        assert repo.downloads == 0
        assert repo.likes == 0
        assert repo.tags == []
        assert repo.private is False


class TestHistoryEntry:
    """Tests for HistoryEntry model."""
    
    def test_create(self):
        """Test creating history entry."""
        entry = HistoryEntry(
            repo_id="user/model",
            save_path="/downloads/model",
            total_bytes=1000000,
            duration_seconds=60,
        )
        assert entry.is_favorite is False
        assert entry.tags == []
        assert entry.completed_at is not None


class TestProfile:
    """Tests for Profile model."""
    
    def test_create(self):
        """Test creating profile."""
        profile = Profile(
            name="My Profile",
            platform=Platform.HUGGINGFACE,
            default_path="/my/downloads",
        )
        assert profile.name == "My Profile"
        assert profile.file_filters == []
