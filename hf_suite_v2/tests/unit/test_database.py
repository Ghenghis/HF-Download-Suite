"""
Tests for database layer.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from hf_suite_v2.core.database import (
    Database, DownloadTable, HistoryTable, ProfileTable,
    LocationTable, LocalModelTable, SettingsTable, get_db
)


class TestDatabase:
    """Tests for Database singleton and operations."""
    
    @pytest.fixture
    def temp_db(self, tmp_path: Path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test.db"
        # Reset singleton for testing
        Database._instance = None
        db = Database(db_path)
        yield db
        # Cleanup
        Database._instance = None
    
    def test_singleton(self, temp_db):
        """Test that Database is a singleton."""
        db1 = Database()
        db2 = Database()
        assert db1 is db2
    
    def test_add_download(self, temp_db):
        """Test adding a download task."""
        task_id = temp_db.add_download({
            "repo_id": "test/model",
            "platform": "huggingface",
            "repo_type": "model",
            "save_path": "/tmp/downloads",
            "priority": 5,
        })
        
        assert task_id is not None
        assert task_id > 0
    
    def test_get_download(self, temp_db):
        """Test retrieving a download."""
        task_id = temp_db.add_download({
            "repo_id": "user/my-model",
            "platform": "huggingface",
            "repo_type": "model",
            "save_path": "/downloads",
        })
        
        download = temp_db.get_download(task_id)
        assert download is not None
        assert download.repo_id == "user/my-model"
        assert download.platform == "huggingface"
    
    def test_get_download_not_found(self, temp_db):
        """Test retrieving non-existent download."""
        download = temp_db.get_download(99999)
        assert download is None
    
    def test_get_pending_downloads(self, temp_db):
        """Test getting pending downloads."""
        # Add some downloads with different statuses
        temp_db.add_download({
            "repo_id": "pending/model1",
            "platform": "huggingface",
            "repo_type": "model",
            "save_path": "/tmp",
            "status": "pending",
            "priority": 3,
        })
        temp_db.add_download({
            "repo_id": "queued/model2",
            "platform": "huggingface",
            "repo_type": "model",
            "save_path": "/tmp",
            "status": "queued",
            "priority": 1,
        })
        temp_db.add_download({
            "repo_id": "completed/model3",
            "platform": "huggingface",
            "repo_type": "model",
            "save_path": "/tmp",
            "status": "completed",
        })
        
        pending = temp_db.get_pending_downloads()
        
        # Should only get pending and queued, ordered by priority
        assert len(pending) == 2
        assert pending[0].priority == 1  # Higher priority first
    
    def test_update_download(self, temp_db):
        """Test updating a download."""
        task_id = temp_db.add_download({
            "repo_id": "test/model",
            "platform": "huggingface",
            "repo_type": "model",
            "save_path": "/tmp",
            "status": "pending",
        })
        
        result = temp_db.update_download(task_id, status="downloading", downloaded_bytes=1000)
        assert result is True
        
        download = temp_db.get_download(task_id)
        assert download.status == "downloading"
        assert download.downloaded_bytes == 1000
    
    def test_delete_download(self, temp_db):
        """Test deleting a download."""
        task_id = temp_db.add_download({
            "repo_id": "delete/me",
            "platform": "huggingface",
            "repo_type": "model",
            "save_path": "/tmp",
        })
        
        result = temp_db.delete_download(task_id)
        assert result is True
        
        download = temp_db.get_download(task_id)
        assert download is None


class TestHistoryOperations:
    """Tests for history operations."""
    
    @pytest.fixture
    def temp_db(self, tmp_path: Path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test_history.db"
        Database._instance = None
        db = Database(db_path)
        yield db
        Database._instance = None
    
    def test_add_to_history(self, temp_db):
        """Test adding to history."""
        history_id = temp_db.add_to_history({
            "repo_id": "user/model",
            "platform": "huggingface",
            "repo_type": "model",
            "save_path": "/downloads/model",
            "total_bytes": 1000000,
        })
        
        assert history_id is not None
        assert history_id > 0
    
    def test_get_history(self, temp_db):
        """Test getting history."""
        # Add some history entries
        for i in range(5):
            temp_db.add_to_history({
                "repo_id": f"user/model{i}",
                "platform": "huggingface",
                "repo_type": "model",
                "save_path": f"/downloads/model{i}",
            })
        
        history = temp_db.get_history(limit=3)
        
        assert len(history) == 3
    
    def test_toggle_favorite(self, temp_db):
        """Test toggling favorite status."""
        history_id = temp_db.add_to_history({
            "repo_id": "user/favorite",
            "platform": "huggingface",
            "repo_type": "model",
            "save_path": "/downloads",
        })
        
        # Toggle to favorite
        result = temp_db.toggle_favorite(history_id)
        assert result is True
        
        # Get history and check
        history = temp_db.get_history(favorites_only=True)
        assert len(history) == 1
        assert history[0].is_favorite is True


class TestSettingsOperations:
    """Tests for settings operations."""
    
    @pytest.fixture
    def temp_db(self, tmp_path: Path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test_settings.db"
        Database._instance = None
        db = Database(db_path)
        yield db
        Database._instance = None
    
    def test_set_and_get_setting(self, temp_db):
        """Test setting and getting a setting."""
        temp_db.set_setting("theme", "dark")
        
        value = temp_db.get_setting("theme")
        assert value == "dark"
    
    def test_get_setting_default(self, temp_db):
        """Test getting a setting with default."""
        value = temp_db.get_setting("nonexistent", "default_value")
        assert value == "default_value"
    
    def test_update_setting(self, temp_db):
        """Test updating an existing setting."""
        temp_db.set_setting("count", "1")
        temp_db.set_setting("count", "2")
        
        value = temp_db.get_setting("count")
        assert value == "2"
    
    def test_get_all_settings(self, temp_db):
        """Test getting all settings."""
        temp_db.set_setting("key1", "value1")
        temp_db.set_setting("key2", "value2")
        
        settings = temp_db.get_all_settings()
        
        assert "key1" in settings
        assert "key2" in settings
        assert settings["key1"] == "value1"


class TestLocalModelOperations:
    """Tests for local model operations."""
    
    @pytest.fixture
    def temp_db(self, tmp_path: Path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test_local.db"
        Database._instance = None
        db = Database(db_path)
        yield db
        Database._instance = None
    
    def test_add_local_model(self, temp_db):
        """Test adding a local model."""
        model_id = temp_db.add_local_model({
            "file_path": "/models/test.safetensors",
            "file_name": "test.safetensors",
            "file_size": 5000000,
            "model_type": "checkpoint",
        })
        
        assert model_id is not None
    
    def test_update_existing_local_model(self, temp_db):
        """Test that adding same path updates instead of creates."""
        # Add first
        temp_db.add_local_model({
            "file_path": "/models/test.safetensors",
            "file_name": "test.safetensors",
            "file_size": 5000000,
            "model_type": "checkpoint",
        })
        
        # Add same path with different size
        temp_db.add_local_model({
            "file_path": "/models/test.safetensors",
            "file_name": "test.safetensors",
            "file_size": 6000000,
            "model_type": "checkpoint",
        })
        
        models = temp_db.get_local_models()
        assert len(models) == 1
        assert models[0].file_size == 6000000
    
    def test_get_local_models_by_type(self, temp_db):
        """Test filtering local models by type."""
        temp_db.add_local_model({
            "file_path": "/models/checkpoint.safetensors",
            "file_name": "checkpoint.safetensors",
            "model_type": "checkpoint",
        })
        temp_db.add_local_model({
            "file_path": "/models/lora.safetensors",
            "file_name": "lora.safetensors",
            "model_type": "lora",
        })
        
        checkpoints = temp_db.get_local_models(model_type="checkpoint")
        loras = temp_db.get_local_models(model_type="lora")
        
        assert len(checkpoints) == 1
        assert len(loras) == 1
        assert checkpoints[0].model_type == "checkpoint"
    
    def test_find_duplicates(self, temp_db):
        """Test finding duplicate models by hash."""
        # Add models with same hash
        temp_db.add_local_model({
            "file_path": "/models/model1.safetensors",
            "file_name": "model1.safetensors",
            "file_hash": "abc123",
        })
        temp_db.add_local_model({
            "file_path": "/other/model2.safetensors",
            "file_name": "model2.safetensors",
            "file_hash": "abc123",
        })
        temp_db.add_local_model({
            "file_path": "/models/unique.safetensors",
            "file_name": "unique.safetensors",
            "file_hash": "xyz789",
        })
        
        duplicates = temp_db.find_duplicates()
        
        assert len(duplicates) == 1
        assert duplicates[0][0] == "abc123"
        assert len(duplicates[0][1]) == 2


class TestLocationOperations:
    """Tests for location operations."""
    
    @pytest.fixture
    def temp_db(self, tmp_path: Path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test_locations.db"
        Database._instance = None
        db = Database(db_path)
        yield db
        Database._instance = None
    
    def test_add_location(self, temp_db):
        """Test adding a location."""
        loc_id = temp_db.add_location({
            "name": "ComfyUI Checkpoints",
            "path": "/comfyui/models/checkpoints",
            "tool_type": "comfyui",
            "model_type": "checkpoints",
        })
        
        assert loc_id is not None
    
    def test_get_locations(self, temp_db):
        """Test getting all locations."""
        temp_db.add_location({"name": "Location A", "path": "/a"})
        temp_db.add_location({"name": "Location B", "path": "/b"})
        
        locations = temp_db.get_locations()
        
        assert len(locations) == 2
        # Should be sorted by name
        assert locations[0].name == "Location A"
    
    def test_delete_location(self, temp_db):
        """Test deleting a location."""
        loc_id = temp_db.add_location({"name": "Delete Me", "path": "/delete"})
        
        result = temp_db.delete_location(loc_id)
        assert result is True
        
        locations = temp_db.get_locations()
        assert len(locations) == 0
