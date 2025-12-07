"""
Platform-specific utility functions.
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional


def get_platform() -> str:
    """
    Get the current platform name.
    
    Returns:
        "windows", "macos", or "linux"
    """
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == "Linux"


def open_folder(path: str) -> bool:
    """
    Open a folder in the system file browser.
    
    Args:
        path: Path to folder or file (will open containing folder)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # If path is a file, get the containing directory
        if os.path.isfile(path):
            path = os.path.dirname(path)
        
        if not os.path.exists(path):
            return False
        
        system = platform.system()
        
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        
        return True
        
    except Exception:
        return False


def open_file(path: str) -> bool:
    """
    Open a file with the default application.
    
    Args:
        path: Path to file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(path):
            return False
        
        system = platform.system()
        
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        
        return True
        
    except Exception:
        return False


def get_app_data_dir(app_name: str = "HFDownloadSuite") -> Path:
    """
    Get the application data directory for the current platform.
    
    Args:
        app_name: Application name for the directory
        
    Returns:
        Path to application data directory
    """
    system = platform.system()
    
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return Path(base) / app_name
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    else:
        # Linux and others - use XDG standard
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return Path(base) / app_name.lower()


def get_cache_dir(app_name: str = "HFDownloadSuite") -> Path:
    """
    Get the cache directory for the current platform.
    
    Args:
        app_name: Application name for the directory
        
    Returns:
        Path to cache directory
    """
    system = platform.system()
    
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return Path(base) / app_name / "Cache"
    elif system == "Darwin":
        return Path.home() / "Library" / "Caches" / app_name
    else:
        base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        return Path(base) / app_name.lower()


def get_config_dir(app_name: str = "HFDownloadSuite") -> Path:
    """
    Get the config directory for the current platform.
    
    Args:
        app_name: Application name for the directory
        
    Returns:
        Path to config directory
    """
    system = platform.system()
    
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return Path(base) / app_name
    elif system == "Darwin":
        return Path.home() / "Library" / "Preferences" / app_name
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return Path(base) / app_name.lower()


def get_downloads_dir() -> Path:
    """
    Get the default downloads directory.
    
    Returns:
        Path to downloads directory
    """
    system = platform.system()
    
    if system == "Windows":
        # Try Windows known folder
        try:
            import ctypes
            from ctypes import wintypes
            
            FOLDERID_Downloads = ctypes.c_char_p(b'{374DE290-123F-4565-9164-39C4925E467B}')
            path_buf = ctypes.create_unicode_buffer(260)
            # This would require more complex COM setup, use fallback
        except Exception:
            pass
    
    # Fallback for all platforms
    return Path.home() / "Downloads"


def get_temp_dir() -> Path:
    """
    Get the system temporary directory.
    
    Returns:
        Path to temp directory
    """
    import tempfile
    return Path(tempfile.gettempdir())
