# HF Download Suite - Implementation Plan

## New Project Structure

```
hf_download_suite/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── pyproject.toml                   # Modern Python packaging
│
├── core/                            # Shared core library
│   ├── __init__.py
│   ├── database.py                  # SQLite ORM layer
│   ├── models.py                    # Data models (Pydantic)
│   ├── config.py                    # Configuration management
│   ├── constants.py                 # Magic strings, defaults
│   ├── events.py                    # Event bus system
│   ├── logger.py                    # Logging setup
│   │
│   ├── download/
│   │   ├── __init__.py
│   │   ├── manager.py               # Download queue manager
│   │   ├── worker.py                # Download worker thread
│   │   ├── huggingface.py           # HF-specific logic
│   │   ├── modelscope.py            # ModelScope logic
│   │   ├── civitai.py               # Future: CivitAI support
│   │   └── progress.py              # Progress tracking
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── hf_api.py                # HuggingFace API wrapper
│   │   ├── ms_api.py                # ModelScope API wrapper
│   │   └── cache.py                 # API response caching
│   │
│   └── utils/
│       ├── __init__.py
│       ├── paths.py                 # Path utilities
│       ├── files.py                 # File operations
│       ├── network.py               # Network utilities
│       └── validators.py            # Input validation
│
├── ui/                              # PyQt6 UI layer
│   ├── __init__.py
│   ├── app.py                       # QApplication setup
│   ├── main_window.py               # Main window shell
│   ├── theme.py                     # Theme management
│   ├── resources.qrc                # Qt resources
│   │
│   ├── widgets/                     # Reusable widgets
│   │   ├── __init__.py
│   │   ├── download_card.py         # Download item widget
│   │   ├── progress_ring.py         # Circular progress
│   │   ├── search_bar.py            # Search input
│   │   ├── model_card.py            # Model preview card
│   │   ├── path_selector.py         # Path picker with presets
│   │   ├── token_input.py           # Secure token widget
│   │   ├── notification.py          # Toast notifications
│   │   ├── icon_button.py           # Icon-based buttons
│   │   └── collapsible.py           # Collapsible sections
│   │
│   ├── tabs/                        # Tab views
│   │   ├── __init__.py
│   │   ├── downloads_tab.py         # Download queue/manager
│   │   ├── browser_tab.py           # Model browser
│   │   ├── history_tab.py           # Download history
│   │   ├── local_tab.py             # Local model manager
│   │   ├── profiles_tab.py          # Profiles & presets
│   │   ├── settings_tab.py          # Settings panel
│   │   └── comfyui_tab.py           # ComfyUI integration
│   │
│   └── dialogs/
│       ├── __init__.py
│       ├── file_selector.py         # Per-file selection dialog
│       ├── profile_editor.py        # Profile creation/edit
│       ├── about.py                 # About dialog
│       └── first_run.py             # First-run setup wizard
│
├── integrations/                    # External tool integrations
│   ├── __init__.py
│   ├── comfyui/
│   │   ├── __init__.py
│   │   ├── detector.py              # Auto-detect ComfyUI
│   │   ├── workflow_parser.py       # Parse workflows for models
│   │   └── paths.py                 # ComfyUI path mapping
│   │
│   └── tools/
│       ├── __init__.py
│       ├── a1111.py                 # Automatic1111 detection
│       ├── forge.py                 # Forge detection
│       └── lmstudio.py              # LM Studio detection
│
├── cli/                             # Command-line interface
│   ├── __init__.py
│   ├── main.py                      # CLI entry point
│   └── commands.py                  # CLI commands
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/
│   │   ├── test_download.py
│   │   ├── test_api.py
│   │   └── test_database.py
│   ├── integration/
│   │   └── test_workflow.py
│   └── ui/
│       └── test_widgets.py
│
├── assets/                          # Static assets
│   ├── icons/                       # SVG icons
│   ├── themes/                      # QSS stylesheets
│   └── fonts/                       # Custom fonts
│
└── docs/                            # Documentation
    ├── README.md
    ├── CONTRIBUTING.md
    ├── API.md
    └── USER_GUIDE.md
```

---

## Database Schema (SQLite)

```sql
-- Downloads table
CREATE TABLE downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id TEXT NOT NULL,
    platform TEXT NOT NULL,  -- 'huggingface', 'modelscope', 'civitai'
    repo_type TEXT NOT NULL, -- 'model', 'dataset', 'space'
    status TEXT DEFAULT 'pending',  -- pending, downloading, paused, completed, failed
    save_path TEXT NOT NULL,
    files_json TEXT,  -- JSON array of selected files
    total_bytes INTEGER DEFAULT 0,
    downloaded_bytes INTEGER DEFAULT 0,
    speed_bps INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 5,  -- 1=highest, 10=lowest
    profile_id INTEGER REFERENCES profiles(id)
);

-- Download files (per-file tracking)
CREATE TABLE download_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    download_id INTEGER REFERENCES downloads(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    downloaded_bytes INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    checksum TEXT,
    verified BOOLEAN DEFAULT FALSE
);

-- History (completed downloads)
CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    repo_type TEXT NOT NULL,
    save_path TEXT NOT NULL,
    total_bytes INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INTEGER,
    is_favorite BOOLEAN DEFAULT FALSE,
    tags TEXT  -- JSON array
);

-- Profiles
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    platform TEXT,
    endpoint TEXT,
    default_path TEXT,
    token_id INTEGER REFERENCES tokens(id),
    file_filters TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tokens (encrypted)
CREATE TABLE tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,
    encrypted_value TEXT NOT NULL,
    scope TEXT,  -- 'read', 'write', 'full'
    last_validated TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE
);

-- Named locations / Presets
CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    tool_type TEXT,  -- 'comfyui', 'a1111', 'lmstudio', 'custom'
    model_type TEXT, -- 'checkpoints', 'loras', 'vae', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Local models (scanned)
CREATE TABLE local_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    file_hash TEXT,
    model_type TEXT,
    source_repo TEXT,
    source_platform TEXT,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT
);

-- Settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_downloads_status ON downloads(status);
CREATE INDEX idx_downloads_platform ON downloads(platform);
CREATE INDEX idx_history_repo ON history(repo_id);
CREATE INDEX idx_history_favorite ON history(is_favorite);
CREATE INDEX idx_local_models_type ON local_models(model_type);
CREATE INDEX idx_local_models_hash ON local_models(file_hash);
```

---

## Key Component Designs

### 1. Download Manager (`core/download/manager.py`)

```python
class DownloadManager:
    """Central download queue manager with worker pool."""
    
    def __init__(self, max_workers: int = 3):
        self.queue: PriorityQueue[DownloadTask] = PriorityQueue()
        self.workers: list[DownloadWorker] = []
        self.active_downloads: dict[int, DownloadTask] = {}
        self.max_workers = max_workers
        self.bandwidth_limit: int | None = None  # bytes/sec
        
    def add(self, task: DownloadTask, priority: int = 5) -> int:
        """Add download to queue, returns task ID."""
        
    def pause(self, task_id: int) -> bool:
        """Pause active download."""
        
    def resume(self, task_id: int) -> bool:
        """Resume paused download."""
        
    def cancel(self, task_id: int) -> bool:
        """Cancel and remove download."""
        
    def set_priority(self, task_id: int, priority: int) -> None:
        """Change task priority."""
        
    def get_status(self) -> ManagerStatus:
        """Get overall manager status."""
        
    # Signals
    task_started = Signal(int)      # task_id
    task_progress = Signal(int, ProgressInfo)
    task_completed = Signal(int, str)  # task_id, path
    task_failed = Signal(int, str)     # task_id, error
    queue_changed = Signal()
```

### 2. Download Card Widget (`ui/widgets/download_card.py`)

```python
class DownloadCard(QFrame):
    """Visual representation of a download task."""
    
    # Layout:
    # ┌─────────────────────────────────────────────────────────┐
    # │ [🤗] model-name                    [⏸] [❌]             │
    # │ username/repo-id                                        │
    # │ ████████████░░░░░░░░░░  45.2% | 1.2 GB / 2.7 GB        │
    # │ ⬇️ 12.5 MB/s | ⏱️ 2m 15s remaining                      │
    # └─────────────────────────────────────────────────────────┘
    
    pause_clicked = Signal(int)  # task_id
    cancel_clicked = Signal(int)
    retry_clicked = Signal(int)
    
    def __init__(self, task: DownloadTask):
        ...
        
    def update_progress(self, info: ProgressInfo) -> None:
        """Update progress bar and stats."""
        
    def set_status(self, status: DownloadStatus) -> None:
        """Update visual state based on status."""
```

### 3. Model Browser (`ui/tabs/browser_tab.py`)

```python
class BrowserTab(QWidget):
    """HuggingFace model browser with search and filters."""
    
    # Layout:
    # ┌─────────────────────────────────────────────────────────┐
    # │ 🔍 [Search models...                    ] [🔽 Filters]  │
    # ├─────────────────────────────────────────────────────────┤
    # │ [Model Card] [Model Card] [Model Card] [Model Card]     │
    # │ [Model Card] [Model Card] [Model Card] [Model Card]     │
    # │ [Model Card] [Model Card] [Model Card] [Model Card]     │
    # ├─────────────────────────────────────────────────────────┤
    # │ ◀ Page 1 of 50 ▶                        [Load More]     │
    # └─────────────────────────────────────────────────────────┘
    
    model_selected = Signal(str)  # repo_id
    add_to_queue = Signal(str, str)  # repo_id, path
    
    def search(self, query: str, filters: SearchFilters) -> None:
        """Search HuggingFace API."""
        
    def show_model_details(self, repo_id: str) -> None:
        """Show model card in detail view."""
```

### 4. Settings Tab (`ui/tabs/settings_tab.py`)

```python
class SettingsTab(QWidget):
    """Comprehensive settings panel."""
    
    # Sections:
    # - Authentication (Tokens)
    # - Download Settings (Workers, Bandwidth, Retries)
    # - Paths & Locations
    # - Network (Proxy, Endpoints)
    # - Appearance (Theme, Font Size)
    # - Advanced (Logging, Debug)
    
    settings_changed = Signal(str, object)  # key, value
    
    def __init__(self):
        self.sections = {
            'auth': AuthSection(),
            'download': DownloadSection(),
            'paths': PathsSection(),
            'network': NetworkSection(),
            'appearance': AppearanceSection(),
            'advanced': AdvancedSection(),
        }
```

---

## Styling System (QSS)

### Theme File Structure

```
assets/themes/
├── dark.qss           # Dark theme
├── light.qss          # Light theme
├── variables.json     # Theme variables
└── base.qss           # Shared base styles
```

### Example Theme Variables

```json
{
  "dark": {
    "bg-primary": "#1e1e2e",
    "bg-secondary": "#313244",
    "bg-tertiary": "#45475a",
    "text-primary": "#cdd6f4",
    "text-secondary": "#a6adc8",
    "accent": "#89b4fa",
    "success": "#a6e3a1",
    "warning": "#f9e2af",
    "error": "#f38ba8",
    "border": "#585b70",
    "shadow": "rgba(0, 0, 0, 0.3)"
  }
}
```

### Base Component Styles

```css
/* Download Card */
DownloadCard {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    margin: 4px;
}

DownloadCard:hover {
    border-color: var(--accent);
    background: var(--bg-tertiary);
}

/* Progress Bar */
QProgressBar {
    background: var(--bg-tertiary);
    border: none;
    border-radius: 4px;
    height: 8px;
}

QProgressBar::chunk {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 var(--accent),
        stop: 1 var(--success)
    );
    border-radius: 4px;
}

/* Tab Bar */
QTabBar::tab {
    background: var(--bg-secondary);
    color: var(--text-secondary);
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: var(--text-primary);
    border-bottom-color: var(--accent);
}
```

---

## Event System (`core/events.py`)

```python
from typing import Callable, Any
from collections import defaultdict
import threading

class EventBus:
    """Application-wide event bus for decoupled communication."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._subscribers = defaultdict(list)
        return cls._instance
    
    def subscribe(self, event: str, callback: Callable) -> None:
        """Subscribe to an event."""
        self._subscribers[event].append(callback)
    
    def unsubscribe(self, event: str, callback: Callable) -> None:
        """Unsubscribe from an event."""
        if callback in self._subscribers[event]:
            self._subscribers[event].remove(callback)
    
    def emit(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all subscribers."""
        for callback in self._subscribers[event]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

# Event constants
class Events:
    # Download events
    DOWNLOAD_QUEUED = "download.queued"
    DOWNLOAD_STARTED = "download.started"
    DOWNLOAD_PROGRESS = "download.progress"
    DOWNLOAD_COMPLETED = "download.completed"
    DOWNLOAD_FAILED = "download.failed"
    DOWNLOAD_CANCELLED = "download.cancelled"
    
    # UI events
    THEME_CHANGED = "ui.theme_changed"
    TAB_CHANGED = "ui.tab_changed"
    NOTIFICATION = "ui.notification"
    
    # Settings events
    SETTINGS_CHANGED = "settings.changed"
    PROFILE_CHANGED = "settings.profile_changed"
    
    # Model events
    MODEL_SCANNED = "model.scanned"
    MODEL_DELETED = "model.deleted"
```

---

## Implementation Order

### Sprint 1: Core Infrastructure (Days 1-5)
1. Set up new project structure
2. Implement database layer
3. Create configuration system
4. Set up event bus
5. Implement logging

### Sprint 2: Download System (Days 6-10)
1. Create DownloadTask model
2. Implement DownloadManager
3. Build DownloadWorker
4. Add HuggingFace downloader
5. Add progress tracking

### Sprint 3: UI Framework (Days 11-15)
1. Create main window shell
2. Implement tab navigation
3. Build base widgets
4. Set up theming system
5. Create DownloadCard widget

### Sprint 4: Downloads Tab (Days 16-20)
1. Build queue view
2. Implement pause/resume
3. Add priority controls
4. Create bulk operations
5. Add keyboard shortcuts

### Sprint 5: Browser Tab (Days 21-25)
1. Implement HF API client
2. Build search UI
3. Create ModelCard widget
4. Add filtering
5. Implement pagination

### Sprint 6: History & Local (Days 26-30)
1. Build history view
2. Add favorites
3. Implement local scanner
4. Add duplicate detection
5. Create file operations

### Sprint 7: Settings & Integration (Days 31-35)
1. Build settings panel
2. Implement profiles
3. Add ComfyUI detection
4. Create workflow parser
5. Build path mapping

### Sprint 8: Polish & Testing (Days 36-40)
1. Write unit tests
2. Create integration tests
3. Performance optimization
4. Documentation
5. Packaging

---

## Dependencies (requirements.txt)

```txt
# Core
PyQt6>=6.6.0
PyQt6-Qt6>=6.6.0
pydantic>=2.5.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0

# Download
huggingface_hub>=0.20.0
aiohttp>=3.9.0
tqdm>=4.66.0
requests>=2.31.0

# Optional platforms
modelscope>=1.11.0

# Utilities
python-dotenv>=1.0.0
platformdirs>=4.1.0
diskcache>=5.6.0
cryptography>=41.0.0

# Development
pytest>=7.4.0
pytest-qt>=4.3.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
ruff>=0.1.0
mypy>=1.7.0
pre-commit>=3.6.0

# Packaging
pyinstaller>=6.3.0
```

---

## Conclusion

This implementation plan provides a complete roadmap to transform the basic HF downloader into a professional-grade application. The modular architecture allows for incremental development while maintaining code quality and testability.

Key architectural decisions:
1. **SQLite** for persistent storage (no external dependencies)
2. **Event bus** for decoupled component communication
3. **Pydantic** for data validation and serialization
4. **Async downloads** for better performance
5. **Widget-based UI** for reusable components
6. **Theme system** for customization

Estimated total development time: **8-10 weeks** with one developer.

