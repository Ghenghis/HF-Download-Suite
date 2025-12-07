"""
Embedded browser widget using QWebEngineView.

Provides an internal Chromium-based browser for:
- Browsing HuggingFace/ModelScope within the app
- OAuth authentication flows
- Model page previews
- Documentation viewing

No external browser redirects - everything stays in-app.
"""

import logging
from typing import Optional, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QPushButton, QProgressBar, QLabel,
    QMenu, QToolBar, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt6.QtGui import QAction

# Try to import WebEngine - it's an optional dependency
# Catch both ImportError and OSError (DLL load failures)
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
    WEBENGINE_AVAILABLE = True
except (ImportError, OSError) as e:
    WEBENGINE_AVAILABLE = False
    QWebEngineView = None
    logger = __import__('logging').getLogger(__name__)
    logger.warning(f"WebEngine not available: {e}")

from ...core import EventBus, Events
from ...core.constants import PLATFORMS

logger = logging.getLogger(__name__)


class EmbeddedBrowser(QWidget):
    """
    Embedded Chromium browser widget.
    
    Features:
    - Navigation bar (back, forward, refresh, URL bar)
    - Progress indicator
    - Download interception (triggers app downloads)
    - Token extraction from HuggingFace auth
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ [←] [→] [🔄] [🏠] [https://huggingface.co/...    ] [⬇️] │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │              [Web Page Content]                         │
    │                                                         │
    ├─────────────────────────────────────────────────────────┤
    │ [████████████████░░░░░░░░] Loading...                   │
    └─────────────────────────────────────────────────────────┘
    
    Signals:
        url_changed: Emitted when URL changes
        title_changed: Emitted when page title changes
        download_requested: Emitted when user clicks download (repo_id, platform)
        token_detected: Emitted when HF token is detected in page
    """
    
    url_changed = pyqtSignal(str)
    title_changed = pyqtSignal(str)
    download_requested = pyqtSignal(str, str)  # repo_id, platform
    token_detected = pyqtSignal(str)  # token value
    
    def __init__(self, parent=None, show_toolbar: bool = True):
        super().__init__(parent)
        
        self.event_bus = EventBus()
        self._show_toolbar = show_toolbar
        
        if not WEBENGINE_AVAILABLE:
            self._setup_fallback_ui()
            return
        
        self._setup_ui()
        self._setup_connections()
        
        # Navigate to default page
        self.navigate_to(PLATFORMS["huggingface"]["models_url"])
    
    def _setup_fallback_ui(self) -> None:
        """Show fallback UI when WebEngine is not available."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon = QLabel("🌐")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel("Embedded Browser Not Available")
        title.setObjectName("sectionTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        message = QLabel(
            "Install PyQt6-WebEngine for integrated browsing:\n\n"
            "pip install PyQt6-WebEngine\n\n"
            "This enables:\n"
            "• Browse HuggingFace within the app\n"
            "• In-app authentication\n"
            "• Model previews without leaving the app"
        )
        message.setObjectName("subtitle")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        install_btn = QPushButton("📦 Install PyQt6-WebEngine")
        install_btn.clicked.connect(self._install_webengine)
        layout.addWidget(install_btn, 0, Qt.AlignmentFlag.AlignCenter)
    
    def _install_webengine(self) -> None:
        """Install WebEngine and auto-restart the app."""
        import subprocess
        import sys
        import os

        try:
            # Show installing message
            self.event_bus.emit(
                Events.NOTIFICATION,
                "Installing PyQt6-WebEngine... Please wait...",
                "info"
            )
            
            # Run pip install synchronously so we can restart after
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "PyQt6-WebEngine"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.event_bus.emit(
                    Events.NOTIFICATION,
                    "Installed! Restarting app...",
                    "success"
                )
                # Auto-restart the application
                QTimer.singleShot(1000, self._restart_app)
            else:
                self.event_bus.emit(
                    Events.NOTIFICATION, 
                    f"Install failed: {result.stderr[:100]}", 
                    "error"
                )
        except Exception as e:
            self.event_bus.emit(Events.NOTIFICATION, f"Install failed: {e}", "error")
    
    def _restart_app(self) -> None:
        """Restart the application to load newly installed modules."""
        import sys
        import os
        
        # Get the current script/executable
        python = sys.executable
        script = sys.argv[0]
        
        # Close current app and start new instance
        QApplication.quit()
        
        os.execl(python, python, script, *sys.argv[1:])
    
    def _setup_ui(self) -> None:
        """Set up the browser UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        if self._show_toolbar:
            layout.addWidget(self._create_toolbar())
        
        # Web view
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.web_view, 1)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
    
    def _create_toolbar(self) -> QFrame:
        """Create the navigation toolbar."""
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setStyleSheet("background-color: #161b22; border-bottom: 1px solid #30363d;")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Back button
        self.back_btn = QPushButton("←")
        self.back_btn.setFixedSize(32, 32)
        self.back_btn.setToolTip("Back")
        self.back_btn.clicked.connect(self._go_back)
        layout.addWidget(self.back_btn)
        
        # Forward button
        self.forward_btn = QPushButton("→")
        self.forward_btn.setFixedSize(32, 32)
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.clicked.connect(self._go_forward)
        layout.addWidget(self.forward_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setToolTip("Refresh")
        self.refresh_btn.clicked.connect(self._refresh)
        layout.addWidget(self.refresh_btn)
        
        # Home button
        self.home_btn = QPushButton("🏠")
        self.home_btn.setFixedSize(32, 32)
        self.home_btn.setToolTip("Home (HuggingFace)")
        self.home_btn.clicked.connect(self._go_home)
        layout.addWidget(self.home_btn)
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL...")
        self.url_bar.returnPressed.connect(self._navigate_to_url_bar)
        layout.addWidget(self.url_bar, 1)
        
        # Quick nav buttons
        hf_btn = QPushButton("🤗")
        hf_btn.setFixedSize(32, 32)
        hf_btn.setToolTip("HuggingFace Models")
        hf_btn.clicked.connect(lambda: self.navigate_to(PLATFORMS["huggingface"]["models_url"]))
        layout.addWidget(hf_btn)
        
        ms_btn = QPushButton("📦")
        ms_btn.setFixedSize(32, 32)
        ms_btn.setToolTip("ModelScope Models")
        ms_btn.clicked.connect(lambda: self.navigate_to(PLATFORMS["modelscope"]["models_url"]))
        layout.addWidget(ms_btn)
        
        # Download current model button
        self.download_btn = QPushButton("⬇️ Download")
        self.download_btn.setToolTip("Download this model")
        self.download_btn.clicked.connect(self._download_current)
        self.download_btn.hide()  # Show only on model pages
        layout.addWidget(self.download_btn)
        
        return toolbar
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        if not WEBENGINE_AVAILABLE:
            return
        
        # URL changed
        self.web_view.urlChanged.connect(self._on_url_changed)
        
        # Title changed
        self.web_view.titleChanged.connect(self._on_title_changed)
        
        # Loading progress
        self.web_view.loadStarted.connect(self._on_load_started)
        self.web_view.loadProgress.connect(self._on_load_progress)
        self.web_view.loadFinished.connect(self._on_load_finished)
        
        # Page content changes
        self.web_view.page().contentsSizeChanged.connect(self._on_content_changed)
    
    def navigate_to(self, url: str) -> None:
        """Navigate to a URL."""
        if not WEBENGINE_AVAILABLE:
            return
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        self.web_view.setUrl(QUrl(url))
    
    def navigate_to_model(self, repo_id: str, platform: str = "huggingface") -> None:
        """Navigate to a model page."""
        platform_info = PLATFORMS.get(platform, PLATFORMS["huggingface"])
        url = f"{platform_info['models_url']}/{repo_id}"
        self.navigate_to(url)
    
    def navigate_to_token_page(self, platform: str = "huggingface") -> None:
        """Navigate to token settings page."""
        platform_info = PLATFORMS.get(platform, PLATFORMS["huggingface"])
        self.navigate_to(platform_info["token_url"])
    
    def _navigate_to_url_bar(self) -> None:
        """Navigate to URL in the URL bar."""
        url = self.url_bar.text().strip()
        if url:
            self.navigate_to(url)
    
    def _go_back(self) -> None:
        """Go back in history."""
        if WEBENGINE_AVAILABLE:
            self.web_view.back()
    
    def _go_forward(self) -> None:
        """Go forward in history."""
        if WEBENGINE_AVAILABLE:
            self.web_view.forward()
    
    def _refresh(self) -> None:
        """Refresh current page."""
        if WEBENGINE_AVAILABLE:
            self.web_view.reload()
    
    def _go_home(self) -> None:
        """Go to home page."""
        self.navigate_to(PLATFORMS["huggingface"]["models_url"])
    
    def _on_url_changed(self, url: QUrl) -> None:
        """Handle URL change."""
        url_str = url.toString()
        self.url_bar.setText(url_str)
        self.url_changed.emit(url_str)
        
        # Update navigation buttons
        self.back_btn.setEnabled(self.web_view.page().history().canGoBack())
        self.forward_btn.setEnabled(self.web_view.page().history().canGoForward())
        
        # Check if on a model page
        self._check_model_page(url_str)
    
    def _on_title_changed(self, title: str) -> None:
        """Handle title change."""
        self.title_changed.emit(title)
    
    def _on_load_started(self) -> None:
        """Handle load start."""
        self.progress_bar.setValue(0)
        self.progress_bar.show()
    
    def _on_load_progress(self, progress: int) -> None:
        """Handle load progress."""
        self.progress_bar.setValue(progress)
    
    def _on_load_finished(self, success: bool) -> None:
        """Handle load finish."""
        self.progress_bar.hide()
        
        if success:
            # Try to detect tokens on HuggingFace settings page
            self._check_for_token()
    
    def _on_content_changed(self) -> None:
        """Handle content size change."""
        pass
    
    def _check_model_page(self, url: str) -> None:
        """Check if current page is a model page and show download button."""
        is_model_page = False
        
        # HuggingFace model page pattern
        if "huggingface.co/" in url:
            parts = url.replace("https://huggingface.co/", "").split("/")
            # Should be username/modelname (not models, datasets, spaces, etc.)
            if len(parts) >= 2 and parts[0] not in ["models", "datasets", "spaces", "docs"]:
                is_model_page = True
        
        # ModelScope model page
        if "modelscope.cn/models/" in url:
            is_model_page = True
        
        self.download_btn.setVisible(is_model_page)
    
    def _check_for_token(self) -> None:
        """Check for HuggingFace token on settings page."""
        url = self.web_view.url().toString()
        
        if "huggingface.co/settings/tokens" in url:
            # Inject JS to extract token if visible
            js = """
            (function() {
                var tokenElements = document.querySelectorAll('code.text-sm');
                for (var el of tokenElements) {
                    var text = el.textContent;
                    if (text.startsWith('hf_')) {
                        return text;
                    }
                }
                return null;
            })();
            """
            self.web_view.page().runJavaScript(js, self._on_token_found)
    
    def _on_token_found(self, token: str) -> None:
        """Handle token found."""
        if token and token.startswith("hf_"):
            self.token_detected.emit(token)
            self.event_bus.emit(
                Events.NOTIFICATION,
                "Token detected! Click 'Use Token' in Settings.",
                "success"
            )
    
    def _download_current(self) -> None:
        """Request download of current model."""
        url = self.web_view.url().toString()
        
        repo_id = None
        platform = "huggingface"
        
        # Parse HuggingFace URL
        if "huggingface.co/" in url:
            path = url.replace("https://huggingface.co/", "").split("?")[0]
            parts = path.split("/")
            if len(parts) >= 2:
                repo_id = f"{parts[0]}/{parts[1]}"
        
        # Parse ModelScope URL
        elif "modelscope.cn/models/" in url:
            path = url.replace("https://modelscope.cn/models/", "").split("?")[0]
            parts = path.split("/")
            if len(parts) >= 2:
                repo_id = f"{parts[0]}/{parts[1]}"
                platform = "modelscope"
        
        if repo_id:
            self.download_requested.emit(repo_id, platform)
            self.event_bus.emit(
                Events.NOTIFICATION,
                f"Preparing download: {repo_id}",
                "info"
            )
    
    def get_current_url(self) -> str:
        """Get current URL."""
        if WEBENGINE_AVAILABLE:
            return self.web_view.url().toString()
        return ""
    
    def get_current_title(self) -> str:
        """Get current page title."""
        if WEBENGINE_AVAILABLE:
            return self.web_view.title()
        return ""


class BrowserDialog(QWidget):
    """
    Standalone browser dialog/window.
    
    Can be used for:
    - OAuth authentication flows
    - Viewing documentation
    - Model page previews
    """
    
    def __init__(self, url: str = None, title: str = "Browser", parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.resize(1000, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = EmbeddedBrowser(show_toolbar=True)
        layout.addWidget(self.browser)
        
        if url:
            self.browser.navigate_to(url)
        
        # Update window title from page title
        self.browser.title_changed.connect(
            lambda t: self.setWindowTitle(f"{t} - {title}" if t else title)
        )
    
    def navigate_to(self, url: str) -> None:
        """Navigate to URL."""
        self.browser.navigate_to(url)


def is_webengine_available() -> bool:
    """Check if WebEngine is available."""
    return WEBENGINE_AVAILABLE
