"""
Tests for configuration management.
"""

import pytest
import json
import tempfile
from pathlib import Path

from hf_suite_v2.core.config import Config, DownloadSettings, NetworkSettings, UISettings


class TestConfig:
    """Tests for Config model."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.download.max_workers == 3
        assert config.download.auto_retry is True
        assert config.network.use_hf_mirror is False
        assert config.ui.theme == "dark"
        assert config.first_run is True
    
    def test_save_and_load(self, tmp_path: Path):
        """Test saving and loading config."""
        config_path = tmp_path / "test_config.json"
        
        # Create and modify config
        config = Config()
        config.download.max_workers = 5
        config.ui.theme = "light"
        config.first_run = False
        
        # Save
        config.save(config_path)
        
        # Verify file exists
        assert config_path.exists()
        
        # Load and verify
        loaded = Config.load(config_path)
        assert loaded.download.max_workers == 5
        assert loaded.ui.theme == "light"
        assert loaded.first_run is False
    
    def test_load_creates_default(self, tmp_path: Path):
        """Test that load creates default config if file doesn't exist."""
        config_path = tmp_path / "nonexistent_config.json"
        
        config = Config.load(config_path)
        
        assert config_path.exists()
        assert config.download.max_workers == 3
    
    def test_update(self, tmp_path: Path):
        """Test updating config values."""
        config_path = tmp_path / "update_test.json"
        config = Config()
        config.save(config_path)
        
        # Update simple field
        config.update(first_run=False)
        assert config.first_run is False
        
        # Save explicitly to test path and verify
        config.save(config_path)
        loaded = Config.load(config_path)
        assert loaded.first_run is False
    
    def test_add_recent_repo(self):
        """Test adding recent repositories."""
        config = Config()
        config.recent_repos = []
        
        config.add_recent_repo("user/model1")
        assert config.recent_repos[0] == "user/model1"
        
        config.add_recent_repo("user/model2")
        assert config.recent_repos[0] == "user/model2"
        assert config.recent_repos[1] == "user/model1"
        
        # Adding existing should move to front
        config.add_recent_repo("user/model1")
        assert config.recent_repos[0] == "user/model1"
        assert config.recent_repos[1] == "user/model2"
    
    def test_recent_repos_limit(self):
        """Test that recent repos are limited to 20."""
        config = Config()
        config.recent_repos = []
        
        for i in range(25):
            config.add_recent_repo(f"user/model{i}")
        
        assert len(config.recent_repos) == 20
        assert config.recent_repos[0] == "user/model24"
    
    def test_get_effective_endpoint(self):
        """Test get_effective_endpoint method."""
        config = Config()
        
        # Default endpoint
        endpoint = config.get_effective_endpoint("huggingface")
        assert endpoint == "https://huggingface.co"
        
        # With mirror
        config.network.use_hf_mirror = True
        endpoint = config.get_effective_endpoint("huggingface")
        assert "hf-mirror.com" in endpoint


class TestDownloadSettings:
    """Tests for DownloadSettings."""
    
    def test_validation(self):
        """Test field validation."""
        settings = DownloadSettings(max_workers=8)
        assert settings.max_workers == 8
        
        # Test bounds
        with pytest.raises(ValueError):
            DownloadSettings(max_workers=0)
        
        with pytest.raises(ValueError):
            DownloadSettings(max_workers=10)


class TestUISettings:
    """Tests for UISettings."""
    
    def test_defaults(self):
        """Test UI defaults."""
        settings = UISettings()
        
        assert settings.theme == "dark"
        assert settings.font_size == 12
        assert settings.show_notifications is True
        assert settings.window_width == 1000
        assert settings.window_height == 700


class TestNetworkSettings:
    """Tests for NetworkSettings."""
    
    def test_defaults(self):
        """Test network defaults."""
        settings = NetworkSettings()
        
        assert settings.use_proxy is False
        assert settings.proxy_url is None
        assert settings.timeout == 300
        assert "huggingface.co" in settings.hf_endpoint
