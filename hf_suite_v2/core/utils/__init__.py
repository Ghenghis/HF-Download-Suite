"""
Core utilities module.

Provides common helper functions for:
- File operations
- Formatting
- Platform detection
- Path handling
"""

from .file_utils import (
    format_bytes,
    format_duration,
    safe_filename,
    ensure_dir,
    get_file_hash,
)
from .platform_utils import (
    get_platform,
    open_folder,
    get_app_data_dir,
    is_windows,
    is_macos,
    is_linux,
)

__all__ = [
    "format_bytes",
    "format_duration",
    "safe_filename",
    "ensure_dir",
    "get_file_hash",
    "get_platform",
    "open_folder",
    "get_app_data_dir",
    "is_windows",
    "is_macos",
    "is_linux",
]
