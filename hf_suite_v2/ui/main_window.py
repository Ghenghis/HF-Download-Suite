"""
Main application window with tab-based navigation.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStatusBar, QLabel, QPushButton,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QIcon, QKeySequence, QShortcut

from ..core import get_config, EventBus, Events
from ..core.download import get_download_manager
from ..core.constants import APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT

from .tabs.downloads_tab import DownloadsTab
from .tabs.browser_tab import BrowserTab
from .tabs.history_tab import HistoryTab
from .tabs.local_models_tab import LocalModelsTab
from .tabs.settings_tab import SettingsTab
from .tabs.profiles_tab import ProfilesTab
from .tabs.comfyui_tab import ComfyUITab

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window with tabbed interface.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │  HF Download Suite                     [─] [□] [×]      │
    ├─────────────────────────────────────────────────────────┤
    │  [📥 Downloads] [🔍 Browser] [📜 History] [⚙ Settings]  │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │                   [Tab Content Area]                    │
    │                                                         │
    ├─────────────────────────────────────────────────────────┤
    │  ⬇️ 2 active | 📊 45.2 MB/s | 💾 1.2 TB free | ✅ Ready │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.event_bus = EventBus()
        self.download_manager = get_download_manager()
        
        self._setup_window()
        self._setup_ui()
        self._setup_connections()
        self._setup_shortcuts()
        self._setup_status_timer()
        
        logger.info("Main window initialized")
    
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Center on screen
        screen = self.screen().geometry()
        x = (screen.width() - self.config.ui.window_width) // 2
        y = (screen.height() - self.config.ui.window_height) // 2
        self.move(x, y)
    
    def _setup_ui(self) -> None:
        """Set up the main UI components."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(False)
        
        # Create tabs
        self.downloads_tab = DownloadsTab()
        self.browser_tab = BrowserTab()
        self.history_tab = HistoryTab()
        self.local_models_tab = LocalModelsTab()
        self.profiles_tab = ProfilesTab()
        self.comfyui_tab = ComfyUITab()
        self.settings_tab = SettingsTab()
        
        # Add tabs with icons
        self.tabs.addTab(self.downloads_tab, "📥 Downloads")
        self.tabs.addTab(self.browser_tab, "🔍 Browser")
        self.tabs.addTab(self.history_tab, "📜 History")
        self.tabs.addTab(self.local_models_tab, "📁 Local")
        self.tabs.addTab(self.profiles_tab, "👤 Profiles")
        self.tabs.addTab(self.comfyui_tab, "🎨 ComfyUI")
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")
        
        # Connect cross-tab signals
        self.browser_tab.download_requested.connect(self._on_browser_download)
        self.history_tab.redownload_requested.connect(self._on_redownload)
        self.comfyui_tab.download_requested.connect(self._on_browser_download)
        
        # Restore last tab
        if 0 <= self.config.last_tab < self.tabs.count():
            self.tabs.setCurrentIndex(self.config.last_tab)
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self._setup_status_bar()
    
    def _create_placeholder(self, name: str) -> QWidget:
        """Create a placeholder widget for unimplemented tabs."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel(f"{name} Tab")
        label.setObjectName("sectionTitle")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        subtitle = QLabel("Coming soon...")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        return widget
    
    def _setup_status_bar(self) -> None:
        """Set up the status bar with proper spacing."""
        self.status_bar = QStatusBar()
        self.status_bar.setContentsMargins(8, 4, 8, 4)
        self.setStatusBar(self.status_bar)
        
        # Create a container widget for left-side items with proper spacing
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)  # Good spacing between items
        
        # Active downloads indicator
        self.active_label = QLabel("⬇️ 0 active")
        self.active_label.setStyleSheet("padding: 0 8px;")
        left_layout.addWidget(self.active_label)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("background-color: #30363d; max-width: 1px;")
        sep1.setFixedWidth(1)
        left_layout.addWidget(sep1)
        
        # Speed indicator
        self.speed_label = QLabel("📊 0 B/s")
        self.speed_label.setStyleSheet("padding: 0 8px;")
        left_layout.addWidget(self.speed_label)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("background-color: #30363d; max-width: 1px;")
        sep2.setFixedWidth(1)
        left_layout.addWidget(sep2)
        
        # Queue indicator
        self.queue_label = QLabel("📋 0 queued")
        self.queue_label.setStyleSheet("padding: 0 8px;")
        left_layout.addWidget(self.queue_label)
        
        self.status_bar.addWidget(left_container)
        
        # Stretch
        self.status_bar.addWidget(QWidget(), 1)
        
        # Status on right side
        self.status_text = QLabel("✅ Ready")
        self.status_text.setStyleSheet("padding: 0 8px; color: #3fb950;")
        self.status_bar.addPermanentWidget(self.status_text)
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Tab change
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Download manager signals
        self.download_manager.task_started.connect(self._update_status)
        self.download_manager.task_completed.connect(self._update_status)
        self.download_manager.task_failed.connect(self._update_status)
        self.download_manager.queue_changed.connect(self._update_status)
        self.download_manager.task_progress.connect(self._on_progress)
        
        # Event bus subscriptions
        self.event_bus.subscribe(Events.NOTIFICATION, self._show_notification)
    
    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Tab navigation: Ctrl+1 through Ctrl+7
        for i in range(min(7, self.tabs.count())):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i+1}"), self)
            shortcut.activated.connect(lambda idx=i: self.tabs.setCurrentIndex(idx))
        
        # Ctrl+N: Focus on new download input (go to Downloads tab)
        shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new.activated.connect(self._shortcut_new_download)
        
        # Ctrl+P: Pause all downloads
        shortcut_pause = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut_pause.activated.connect(self._shortcut_pause_all)
        
        # Ctrl+Shift+P: Resume all downloads
        shortcut_resume = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        shortcut_resume.activated.connect(self._shortcut_resume_all)
        
        # Ctrl+, (comma): Open settings
        shortcut_settings = QShortcut(QKeySequence("Ctrl+,"), self)
        shortcut_settings.activated.connect(lambda: self.tabs.setCurrentWidget(self.settings_tab))
        
        # F5: Refresh current tab
        shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        shortcut_refresh.activated.connect(self._shortcut_refresh)
        
        # Ctrl+Q: Quit application
        shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        shortcut_quit.activated.connect(self.close)
        
        # Ctrl+F: Focus search (if available in current tab)
        shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_search.activated.connect(self._shortcut_search)
        
        logger.debug("Keyboard shortcuts initialized")
    
    def _shortcut_new_download(self) -> None:
        """Handle Ctrl+N shortcut."""
        self.tabs.setCurrentWidget(self.downloads_tab)
        # Focus the repo input if available
        if hasattr(self.downloads_tab, 'repo_input'):
            self.downloads_tab.repo_input.setFocus()
    
    def _shortcut_pause_all(self) -> None:
        """Handle Ctrl+P shortcut - pause all downloads."""
        self.download_manager.pause_all()
        self.event_bus.emit(Events.NOTIFICATION, "All downloads paused", "info")
    
    def _shortcut_resume_all(self) -> None:
        """Handle Ctrl+Shift+P shortcut - resume all downloads."""
        self.download_manager.resume_all()
        self.event_bus.emit(Events.NOTIFICATION, "All downloads resumed", "info")
    
    def _shortcut_refresh(self) -> None:
        """Handle F5 shortcut - refresh current tab."""
        current = self.tabs.currentWidget()
        if hasattr(current, 'refresh'):
            current.refresh()
        elif hasattr(current, '_load_history'):
            current._load_history()
        elif hasattr(current, '_scan_models'):
            current._scan_models()
    
    def _shortcut_search(self) -> None:
        """Handle Ctrl+F shortcut - focus search."""
        current = self.tabs.currentWidget()
        if hasattr(current, 'search_input'):
            current.search_input.setFocus()
            current.search_input.selectAll()
    
    def _setup_status_timer(self) -> None:
        """Set up timer for status updates."""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # Update every second
    
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        self.config.update(last_tab=index)
        self.event_bus.emit(Events.TAB_CHANGED, tab_index=index)
    
    def _on_progress(self, progress) -> None:
        """Handle download progress update."""
        self.speed_label.setText(f"📊 {progress.speed_formatted}")
    
    def _update_status(self, *args) -> None:
        """Update status bar information."""
        status = self.download_manager.get_status()
        
        self.active_label.setText(f"⬇️ {status['active_count']} active")
        self.queue_label.setText(f"📋 {status['queue_size']} queued")
        
        if status['active_count'] > 0:
            self.status_text.setText("🔄 Downloading...")
        else:
            self.status_text.setText("✅ Ready")
    
    def _show_notification(self, message: str, level: str = "info") -> None:
        """Show a notification in the status bar."""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
        }
        icon = icons.get(level, "ℹ️")
        self.status_text.setText(f"{icon} {message}")
    
    def _on_browser_download(self, repo_id: str, platform: str) -> None:
        """Handle download request from browser tab."""
        # Switch to downloads tab and add the download
        self.tabs.setCurrentIndex(0)
        self.downloads_tab.repo_input.setText(repo_id)
        
        # Set platform
        for i in range(self.downloads_tab.platform_combo.count()):
            if self.downloads_tab.platform_combo.itemData(i) == platform:
                self.downloads_tab.platform_combo.setCurrentIndex(i)
                break
    
    def _on_redownload(self, repo_id: str, platform: str, path: str) -> None:
        """Handle re-download request from history tab."""
        self.tabs.setCurrentIndex(0)
        self.downloads_tab.repo_input.setText(repo_id)
        self.downloads_tab.path_input.setText(path)
        
        for i in range(self.downloads_tab.platform_combo.count()):
            if self.downloads_tab.platform_combo.itemData(i) == platform:
                self.downloads_tab.platform_combo.setCurrentIndex(i)
                break
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close."""
        # Stop downloads gracefully
        if self.download_manager.get_status()["active_count"] > 0:
            # Could show confirmation dialog here
            pass
        
        # Save config
        self.config.update(
            **{
                "ui.window_width": self.width(),
                "ui.window_height": self.height(),
                "ui.window_x": self.x(),
                "ui.window_y": self.y(),
            }
        )
        
        logger.info("Main window closed")
        event.accept()
