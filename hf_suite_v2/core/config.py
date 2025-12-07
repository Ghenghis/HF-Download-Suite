"""
Configuration management with validation.
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

from .constants import APP_DATA_DIR, DEFAULT_MAX_WORKERS, PLATFORMS

logger = logging.getLogger(__name__)

CONFIG_FILE = APP_DATA_DIR / "config.json"


class DownloadSettings(BaseModel):
    """Download-related settings."""
    max_workers: int = Field(default=DEFAULT_MAX_WORKERS, ge=1, le=8)
    bandwidth_limit: Optional[int] = None  # bytes/sec, None = unlimited
    auto_retry: bool = True
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    verify_checksums: bool = True
    open_folder_after: bool = True
    auto_cleanup_cache: bool = True


class NetworkSettings(BaseModel):
    """Network-related settings."""
    use_proxy: bool = False
    proxy_url: Optional[str] = None
    timeout: int = 300  # seconds
    hf_endpoint: str = PLATFORMS["huggingface"]["default_endpoint"]
    use_hf_mirror: bool = False
    ms_endpoint: str = PLATFORMS["modelscope"]["default_endpoint"]


class UISettings(BaseModel):
    """UI-related settings."""
    theme: str = "dark"  # 'dark', 'light', 'system'
    font_size: int = 12
    show_notifications: bool = True
    notification_duration: int = 5000  # ms
    remember_window_size: bool = True
    window_width: int = 1000
    window_height: int = 700
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    sidebar_visible: bool = True
    show_speed_graph: bool = True
    minimize_to_tray: bool = True  # Show system tray icon
    close_to_tray: bool = False  # Close to tray instead of quitting


class PathSettings(BaseModel):
    """Path-related settings."""
    default_save_path: str = ""
    comfy_root: str = ""
    a1111_root: str = ""
    lmstudio_models: str = ""
    last_browse_path: str = ""


class Config(BaseModel):
    """Main configuration model."""
    
    download: DownloadSettings = Field(default_factory=DownloadSettings)
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    ui: UISettings = Field(default_factory=UISettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    
    # Simple key-value settings
    first_run: bool = True
    last_tab: int = 0
    recent_repos: List[str] = Field(default_factory=list, max_length=20)
    
    model_config = ConfigDict(extra="allow")  # Allow additional fields
    
    @classmethod
    def load(cls, path: Path = None) -> "Config":
        """Load config from file, creating defaults if needed."""
        config_path = path or CONFIG_FILE
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Loaded config from {config_path}")
                return cls(**data)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
        
        # Create default config
        config = cls()
        config.save(config_path)
        return config
    
    def save(self, path: Path = None) -> None:
        """Save config to file."""
        config_path = path or CONFIG_FILE
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.model_dump(), f, indent=2, default=str)
            logger.debug(f"Saved config to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def update(self, **kwargs) -> None:
        """Update config values and save."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif "." in key:
                # Handle nested keys like "download.max_workers"
                parts = key.split(".")
                obj = self
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, parts[-1], value)
        self.save()
    
    def add_recent_repo(self, repo_id: str) -> None:
        """Add repo to recent list (most recent first)."""
        if repo_id in self.recent_repos:
            self.recent_repos.remove(repo_id)
        self.recent_repos.insert(0, repo_id)
        self.recent_repos = self.recent_repos[:20]  # Keep last 20
        self.save()
    
    def get_effective_endpoint(self, platform: str) -> str:
        """Get the effective endpoint URL for a platform."""
        if platform == "huggingface":
            if self.network.use_hf_mirror:
                return PLATFORMS["huggingface"]["mirror_endpoint"]
            return self.network.hf_endpoint
        elif platform == "modelscope":
            return self.network.ms_endpoint
        return PLATFORMS.get(platform, {}).get("default_endpoint", "")


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.load()
    return _config_instance


def reset_config() -> Config:
    """Reset config to defaults."""
    global _config_instance
    _config_instance = Config()
    _config_instance.save()
    return _config_instance
