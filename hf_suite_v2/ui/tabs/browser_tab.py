"""
Browser tab - Integrated browser for HuggingFace/ModelScope.

Features:
- Embedded Chromium browser (no external redirects)
- In-app model browsing
- Direct download integration
- Token detection from auth pages
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QScrollArea, QGridLayout, QSizePolicy, QSpacerItem,
    QStackedWidget, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ...core import get_config, EventBus, Events
from ...core.constants import PLATFORMS
from ...core.models import RepoInfo
from ..widgets.model_card import ModelCard
from ..widgets.embedded_browser import EmbeddedBrowser, is_webengine_available

logger = logging.getLogger(__name__)


class SearchWorker(QThread):
    """Background worker for searching repositories."""
    
    results_ready = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, query: str, platform: str, filters: Dict):
        super().__init__()
        self.query = query
        self.platform = platform
        self.filters = filters
    
    def run(self):
        try:
            results = self._search()
            self.results_ready.emit(results)
        except Exception as e:
            self.error.emit(str(e))
    
    def _search(self) -> List[RepoInfo]:
        """Perform the search."""
        from huggingface_hub import HfApi, ModelFilter
        
        api = HfApi()
        models = []
        
        try:
            # Build filter
            model_filter = ModelFilter()
            
            # Apply filters
            if self.filters.get("task"):
                model_filter.task = self.filters["task"]
            if self.filters.get("library"):
                model_filter.library = self.filters["library"]
            
            # Search
            results = api.list_models(
                search=self.query,
                filter=model_filter,
                limit=50,
                sort="downloads",
                direction=-1,
            )
            
            for model in results:
                models.append(RepoInfo(
                    repo_id=model.id,
                    platform="huggingface",
                    repo_type="model",
                    author=model.id.split("/")[0] if "/" in model.id else "",
                    name=model.id.split("/")[-1] if "/" in model.id else model.id,
                    downloads=model.downloads or 0,
                    likes=model.likes or 0,
                    tags=list(model.tags) if model.tags else [],
                    last_modified=model.lastModified if hasattr(model, 'lastModified') else None,
                    private=model.private if hasattr(model, 'private') else False,
                    gated=model.gated if hasattr(model, 'gated') else False,
                ))
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
        
        return models


class BrowserTab(QWidget):
    """
    Integrated browser tab with embedded Chromium.
    
    Features:
    - Full embedded web browser (no external redirects)
    - Browse HuggingFace/ModelScope directly in-app
    - Direct download button integration
    - Token detection for easy authentication
    - Fallback search mode when WebEngine unavailable
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ [🌐 Web Browse] [🔍 Quick Search]                       │
    ├─────────────────────────────────────────────────────────┤
    │ [←] [→] [🔄] [🏠] [https://huggingface.co/...] [⬇️]    │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │              [Embedded Web Content]                     │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
    """
    
    download_requested = pyqtSignal(str, str)  # repo_id, platform
    
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.event_bus = EventBus()
        self._search_worker: Optional[SearchWorker] = None
        self._model_cards: List[ModelCard] = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI with embedded browser as primary."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tabbed interface: Web Browse | Quick Search
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setDocumentMode(True)
        
        # Tab 1: Embedded Browser (Primary)
        self.browser_widget = self._create_browser_mode()
        self.mode_tabs.addTab(self.browser_widget, "🌐 Web Browse")
        
        # Tab 2: Quick Search (Fallback/Alternative)
        self.search_widget = self._create_search_mode()
        self.mode_tabs.addTab(self.search_widget, "🔍 Quick Search")
        
        layout.addWidget(self.mode_tabs)
    
    def _create_browser_mode(self) -> QWidget:
        """Create the embedded browser mode."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Embedded browser
        self.embedded_browser = EmbeddedBrowser(show_toolbar=True)
        
        # Connect browser signals
        self.embedded_browser.download_requested.connect(self._on_browser_download)
        self.embedded_browser.token_detected.connect(self._on_token_detected)
        
        layout.addWidget(self.embedded_browser)
        
        return widget
    
    def _create_search_mode(self) -> QWidget:
        """Create the quick search mode (fallback)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Search section
        layout.addWidget(self._create_search_section())
        
        # Filters section
        layout.addWidget(self._create_filters_section())
        
        # Results header
        self.results_header = QLabel("Search for models to get started")
        self.results_header.setObjectName("sectionTitle")
        layout.addWidget(self.results_header)
        
        # Results grid in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.results_container = QWidget()
        self.results_layout = QGridLayout(self.results_container)
        self.results_layout.setSpacing(16)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.results_container)
        layout.addWidget(scroll, 1)
        
        return widget
    
    def _create_search_section(self) -> QFrame:
        """Create the search input section."""
        frame = QFrame()
        frame.setObjectName("card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Platform selector
        self.platform_combo = QComboBox()
        for key, info in PLATFORMS.items():
            self.platform_combo.addItem(info["name"], key)
        self.platform_combo.setFixedWidth(140)
        layout.addWidget(self.platform_combo)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search models... (e.g., stable diffusion, llama, whisper)")
        self.search_input.returnPressed.connect(self._do_search)
        layout.addWidget(self.search_input, 1)
        
        # Search button
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setObjectName("primaryButton")
        self.search_btn.setFixedWidth(100)
        self.search_btn.clicked.connect(self._do_search)
        layout.addWidget(self.search_btn)
        
        return frame
    
    def _create_filters_section(self) -> QFrame:
        """Create the filters section."""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Task filter
        layout.addWidget(QLabel("Task:"))
        self.task_combo = QComboBox()
        self.task_combo.addItems([
            "All Tasks",
            "text-generation",
            "text-to-image",
            "image-classification",
            "audio-to-audio",
            "automatic-speech-recognition",
        ])
        self.task_combo.setFixedWidth(180)
        layout.addWidget(self.task_combo)
        
        # Library filter
        layout.addWidget(QLabel("Library:"))
        self.library_combo = QComboBox()
        self.library_combo.addItems([
            "All Libraries",
            "diffusers",
            "transformers",
            "pytorch",
            "safetensors",
        ])
        self.library_combo.setFixedWidth(150)
        layout.addWidget(self.library_combo)
        
        # Sort
        layout.addWidget(QLabel("Sort:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Downloads", "Likes", "Updated"])
        self.sort_combo.setFixedWidth(120)
        layout.addWidget(self.sort_combo)
        
        layout.addStretch()
        
        return frame
    
    def _do_search(self) -> None:
        """Execute the search."""
        query = self.search_input.text().strip()
        if not query:
            return
        
        # Clear previous results
        self._clear_results()
        
        self.results_header.setText("Searching...")
        self.search_btn.setEnabled(False)
        
        # Build filters
        filters = {}
        if self.task_combo.currentIndex() > 0:
            filters["task"] = self.task_combo.currentText()
        if self.library_combo.currentIndex() > 0:
            filters["library"] = self.library_combo.currentText()
        
        # Start search worker
        self._search_worker = SearchWorker(
            query=query,
            platform=self.platform_combo.currentData(),
            filters=filters,
        )
        self._search_worker.results_ready.connect(self._on_results)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.start()
    
    def _on_results(self, results: List[RepoInfo]) -> None:
        """Handle search results."""
        self.search_btn.setEnabled(True)
        
        if not results:
            self.results_header.setText("No results found")
            return
        
        self.results_header.setText(f"{len(results)} results found")
        
        # Create model cards in grid (3 columns)
        for i, repo in enumerate(results):
            card = ModelCard(repo)
            card.download_clicked.connect(self._on_download_clicked)
            card.view_clicked.connect(self._on_view_clicked)  # Internal browser navigation
            
            row = i // 3
            col = i % 3
            self.results_layout.addWidget(card, row, col)
            self._model_cards.append(card)
    
    def _on_search_error(self, error: str) -> None:
        """Handle search error."""
        self.search_btn.setEnabled(True)
        self.results_header.setText(f"Search failed: {error}")
        self.event_bus.emit(Events.NOTIFICATION, f"Search failed: {error}", "error")
    
    def _on_download_clicked(self, repo_id: str) -> None:
        """Handle download request from model card."""
        platform = self.platform_combo.currentData()
        self.download_requested.emit(repo_id, platform)
    
    def _on_view_clicked(self, repo_id: str) -> None:
        """Handle view request - navigate in internal embedded browser."""
        platform = self.platform_combo.currentData()
        self.navigate_to_model(repo_id, platform)
    
    def _clear_results(self) -> None:
        """Clear all result cards."""
        for card in self._model_cards:
            card.setParent(None)
            card.deleteLater()
        self._model_cards.clear()
    
    def _on_browser_download(self, repo_id: str, platform: str) -> None:
        """Handle download request from embedded browser."""
        self.download_requested.emit(repo_id, platform)
    
    def _on_token_detected(self, token: str) -> None:
        """Handle token detection from browser."""
        self.event_bus.emit(Events.TOKEN_UPDATED, token=token, platform="huggingface")
    
    def navigate_to_model(self, repo_id: str, platform: str = "huggingface") -> None:
        """Navigate the embedded browser to a model page."""
        if hasattr(self, 'embedded_browser'):
            self.embedded_browser.navigate_to_model(repo_id, platform)
            self.mode_tabs.setCurrentIndex(0)  # Switch to browser tab
    
    def navigate_to_url(self, url: str) -> None:
        """Navigate the embedded browser to a URL."""
        if hasattr(self, 'embedded_browser'):
            self.embedded_browser.navigate_to(url)
            self.mode_tabs.setCurrentIndex(0)
