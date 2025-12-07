"""
HF Download Suite - Core Module.

This module provides core functionality including:
- Configuration management (Config)
- Database operations (Database)
- Event bus for decoupled communication (EventBus)
- Logging setup (setup_logging)
"""

from .config import Config, get_config
from .database import Database, get_db
# Alias for backward compatibility
get_database = get_db
from .events import EventBus, Events, get_event_bus
from .logger import get_logger, setup_logging
from .exceptions import (
    HFSuiteError,
    InsufficientSpaceError,
    AuthenticationError,
    NetworkError,
    RepositoryNotFoundError,
    GatedModelError,
    DownloadInterruptedError,
    FileVerificationError,
)

__all__ = [
    # Configuration
    "Config",
    "get_config",
    # Database
    "Database",
    "get_db",
    "get_database",  # Alias for backward compatibility
    # Events
    "EventBus",
    "Events",
    "get_event_bus",
    # Logging
    "get_logger",
    "setup_logging",
    # Exceptions
    "HFSuiteError",
    "InsufficientSpaceError",
    "AuthenticationError",
    "NetworkError",
    "RepositoryNotFoundError",
    "GatedModelError",
    "DownloadInterruptedError",
    "FileVerificationError",
]
