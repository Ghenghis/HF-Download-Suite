"""
HF Download Suite v2

A comprehensive HuggingFace model downloader with:
- Multi-download queue management
- Pause/Resume support
- Progress tracking with speed/ETA
- Multi-platform support (HuggingFace, ModelScope)
- ComfyUI integration
- Modern tabbed UI

Usage:
    from hf_suite_v2 import run_app
    run_app()

Or run directly:
    python -m hf_suite_v2
"""

__version__ = "2.0.0"
__author__ = "HF Suite Team"

from .ui.app import run_app, create_app
from .core import get_config, get_db, EventBus, Events

__all__ = [
    "run_app",
    "create_app", 
    "get_config",
    "get_db",
    "EventBus",
    "Events",
    "__version__",
]
