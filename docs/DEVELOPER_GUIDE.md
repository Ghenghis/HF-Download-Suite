# HF Download Suite - Developer Guide

Technical documentation for developers contributing to HF Download Suite.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [UI Components](#ui-components)
- [Event System](#event-system)
- [Database](#database)
- [Testing](#testing)
- [Coding Standards](#coding-standards)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      UI Layer (PyQt6)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Downloads│ │ Search  │ │ History │ │Settings │  ...      │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
└───────┼──────────┼──────────┼──────────┼───────────────────┘
        │          │          │          │
┌───────┼──────────┼──────────┼──────────┼───────────────────┐
│       ▼          ▼          ▼          ▼                   │
│                    Event Bus (Pub/Sub)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                   Core Layer                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │DownloadManager│ │   Config    │ │   Database   │        │
│  └──────┬───────┘ └──────────────┘ └──────────────┘        │
│         │                                                   │
│  ┌──────▼───────┐ ┌──────────────┐ ┌──────────────┐        │
│  │DownloadWorker│ │   API Cache  │ │  Exceptions  │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: UI, business logic, and data access are separate
2. **Event-Driven**: Components communicate via EventBus, not direct coupling
3. **Singleton Services**: Config, Database, DownloadManager are singletons
4. **Thread Safety**: Downloads run in QThreads, database uses thread-local sessions

---

## Project Structure

```
hf_suite_v2/
├── __init__.py
├── __main__.py              # Entry point
├── core/                    # Business logic
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── constants.py         # App constants
│   ├── database.py          # SQLite database
│   ├── events.py            # Event bus system
│   ├── exceptions.py        # Custom exceptions
│   ├── models.py            # Data models
│   ├── api/                 # API clients
│   │   ├── cache.py         # Response caching
│   │   ├── huggingface.py   # HF API wrapper
│   │   └── modelscope.py    # MS API wrapper
│   └── download/            # Download system
│       ├── manager.py       # Queue management
│       └── worker.py        # Download worker
├── ui/                      # User interface
│   ├── app.py               # Application setup
│   ├── main_window.py       # Main window
│   ├── theme.py             # Theming
│   ├── tabs/                # Tab widgets
│   │   ├── downloads_tab.py
│   │   ├── search_tab.py
│   │   ├── history_tab.py
│   │   ├── settings_tab.py
│   │   └── comfyui_tab.py
│   └── widgets/             # Reusable widgets
│       ├── download_card.py
│       ├── path_selector.py
│       └── notification_toast.py
├── integrations/            # External integrations
│   └── comfyui/
│       ├── parser.py        # Workflow parser
│       └── resolver.py      # Model resolver
└── tests/                   # Test suite
    ├── unit/
    └── integration/
```

---

## Core Components

### Config (`core/config.py`)

Pydantic-based configuration with automatic validation and persistence.

```python
from hf_suite_v2.core import get_config

config = get_config()

# Read settings
max_workers = config.download.max_workers
theme = config.ui.theme

# Update settings
config.update(**{"download.max_workers": 4})
config.save()
```

### Database (`core/database.py`)

SQLite database with SQLAlchemy ORM. Singleton pattern with thread-safe sessions.

```python
from hf_suite_v2.core import get_database

db = get_database()

# Add download
task_id = db.add_download({
    "repo_id": "user/model",
    "platform": "huggingface",
    "status": "queued"
})

# Query downloads
downloads = db.get_downloads(status="completed")
```

### DownloadManager (`core/download/manager.py`)

Manages download queue and worker threads.

```python
from hf_suite_v2.core.download import get_download_manager

manager = get_download_manager()

# Add download
task_id = manager.add(
    repo_id="stabilityai/sdxl-turbo",
    save_path="/models/checkpoints",
    platform="huggingface"
)

# Control downloads
manager.pause(task_id)
manager.resume(task_id)
manager.cancel(task_id)

# Bulk operations
manager.pause_all()
manager.resume_all()
```

### Exceptions (`core/exceptions.py`)

Custom exception hierarchy with built-in recovery suggestions.

```python
from hf_suite_v2.core.exceptions import (
    DownloadError,
    InsufficientSpaceError,
    AuthenticationError
)

try:
    download_file()
except InsufficientSpaceError as e:
    print(e.suggestion)  # "Free up disk space or choose a different location"
    print(e.is_retryable)  # False
```

### API Cache (`core/api/cache.py`)

TTL-based caching for API responses.

```python
from hf_suite_v2.core.api import get_cache, cached, TTL_SEARCH

# Direct cache usage
cache = get_cache()
cache.set("key", data, ttl=3600)
result = cache.get("key")

# Decorator usage
@cached("search_models", ttl=TTL_SEARCH)
def search_models(query: str) -> list:
    return api.search(query)
```

---

## UI Components

### Reusable Widgets

#### PathSelector

```python
from hf_suite_v2.ui.widgets import PathSelector, SavePathSelector

# Basic usage
selector = PathSelector(
    placeholder="Select directory...",
    mode="directory",
    validate=True
)
selector.path_changed.connect(self.on_path_changed)

# Convenience class
save_selector = SavePathSelector(initial_path="/models")
```

#### NotificationToast

```python
from hf_suite_v2.ui.widgets import NotificationManager

# In main window
self.notifications = NotificationManager(self)

# Show notifications
self.notifications.show_success("Download complete!")
self.notifications.show_error("Connection failed")
self.notifications.show_warning("Low disk space")
self.notifications.show_info("Checking for updates...")
```

### Creating New Tabs

1. Create `ui/tabs/my_tab.py`:

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from ...core import EventBus, Events

class MyTab(QWidget):
    def __init__(self):
        super().__init__()
        self.event_bus = EventBus()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        # Add widgets...
    
    def refresh(self):
        """Called when tab is activated or F5 pressed."""
        pass
```

2. Register in `main_window.py`:

```python
from .tabs.my_tab import MyTab

# In _setup_tabs()
self.my_tab = MyTab()
self.tab_widget.addTab(self.my_tab, "My Tab")
```

---

## Event System

Decoupled communication between components using publish/subscribe.

### Available Events

| Event | Data | Description |
|-------|------|-------------|
| `DOWNLOAD_STARTED` | task_id | Download began |
| `DOWNLOAD_PROGRESS` | task_id, progress, speed | Progress update |
| `DOWNLOAD_COMPLETED` | task_id | Download finished |
| `DOWNLOAD_FAILED` | task_id, error | Download failed |
| `NOTIFICATION` | message, type | Show notification |
| `SETTINGS_CHANGED` | None | Settings updated |

### Usage

```python
from hf_suite_v2.core import EventBus, Events

class MyComponent:
    def __init__(self):
        self.event_bus = EventBus()
        
        # Subscribe to events
        self.event_bus.subscribe(Events.DOWNLOAD_COMPLETED, self.on_download_complete)
    
    def on_download_complete(self, task_id):
        print(f"Download {task_id} completed!")
    
    def do_something(self):
        # Emit events
        self.event_bus.emit(Events.NOTIFICATION, "Hello!", "info")
```

---

## Database

### Schema

```sql
-- Downloads table
CREATE TABLE downloads (
    id INTEGER PRIMARY KEY,
    repo_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    repo_type TEXT DEFAULT 'model',
    status TEXT DEFAULT 'queued',
    save_path TEXT,
    progress REAL DEFAULT 0,
    total_size INTEGER,
    downloaded_size INTEGER,
    error_message TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- History table
CREATE TABLE history (
    id INTEGER PRIMARY KEY,
    repo_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    save_path TEXT,
    file_count INTEGER,
    total_size INTEGER,
    completed_at TIMESTAMP
);
```

### Migrations

Add new migrations in `core/migrations/`:

```python
# core/migrations/002_add_column.py
def upgrade(engine):
    with engine.connect() as conn:
        conn.execute("ALTER TABLE downloads ADD COLUMN priority INTEGER DEFAULT 5")
```

---

## Testing

### Running Tests

```bash
# All tests
pytest hf_suite_v2/tests -v

# Specific test file
pytest hf_suite_v2/tests/unit/test_exceptions.py -v

# With coverage
pytest hf_suite_v2/tests --cov=hf_suite_v2 --cov-report=html
```

### Writing Tests

```python
# tests/unit/test_my_feature.py
import pytest
from hf_suite_v2.core import MyClass

class TestMyClass:
    def setup_method(self):
        """Run before each test."""
        self.instance = MyClass()
    
    def test_basic_functionality(self):
        result = self.instance.do_something()
        assert result == expected
    
    @pytest.mark.parametrize("input,expected", [
        ("a", 1),
        ("b", 2),
    ])
    def test_with_parameters(self, input, expected):
        assert self.instance.process(input) == expected
```

---

## Coding Standards

### Style Guide

- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use docstrings for public methods

### Docstring Format

```python
def download_file(url: str, path: Path, chunk_size: int = 8192) -> bool:
    """
    Download a file from URL to local path.
    
    Args:
        url: The URL to download from
        path: Local path to save the file
        chunk_size: Size of download chunks in bytes
        
    Returns:
        True if download successful, False otherwise
        
    Raises:
        DownloadError: If the download fails
        InsufficientSpaceError: If not enough disk space
    """
```

### Import Order

```python
# Standard library
import os
import logging
from pathlib import Path

# Third-party
from PyQt6.QtWidgets import QWidget
from huggingface_hub import HfApi

# Local imports
from ..core import get_config
from .widgets import PathSelector
```

### Error Handling

```python
# Use specific exceptions
from hf_suite_v2.core.exceptions import DownloadError

try:
    result = risky_operation()
except DownloadError as e:
    logger.error(f"Download failed: {e}")
    self.event_bus.emit(Events.NOTIFICATION, str(e), "error")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

---

*Last updated: December 2024*
