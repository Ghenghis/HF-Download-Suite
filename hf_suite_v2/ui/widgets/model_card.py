"""
Model card widget - Visual representation of a repository in browser.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...core.models import RepoInfo
from ...core.constants import PLATFORMS

logger = logging.getLogger(__name__)


class ModelCard(QFrame):
    """
    Visual card representing a model in the browser.
    
    Layout:
    ┌─────────────────────────────────────────┐
    │ [🤗] model-name                         │
    │ author/repo-id                          │
    │                                         │
    │ 📥 1.2M downloads  ❤️ 456 likes         │
    │                                         │
    │ [diffusers] [pytorch] [safetensors]     │
    │                                         │
    │ [View on HF]           [⬇️ Download]   │
    └─────────────────────────────────────────┘
    """
    
    download_clicked = pyqtSignal(str)  # repo_id
    view_clicked = pyqtSignal(str)  # repo_id
    
    def __init__(self, repo: RepoInfo):
        super().__init__()
        
        self.repo = repo
        
        self.setObjectName("card")
        self.setFixedHeight(180)
        self.setMinimumWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header: icon + name
        header = QHBoxLayout()
        header.setSpacing(8)
        
        # Platform icon
        icon_label = QLabel(self._get_platform_emoji())
        icon_label.setFixedSize(24, 24)
        header.addWidget(icon_label)
        
        # Model name
        name_label = QLabel(self.repo.display_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        name_label.setWordWrap(True)
        header.addWidget(name_label, 1)
        
        layout.addLayout(header)
        
        # Author/repo
        repo_label = QLabel(self.repo.repo_id)
        repo_label.setObjectName("subtitle")
        layout.addWidget(repo_label)
        
        # Stats
        stats_layout = QHBoxLayout()
        
        downloads_label = QLabel(f"📥 {self._format_number(self.repo.downloads)}")
        stats_layout.addWidget(downloads_label)
        
        likes_label = QLabel(f"❤️ {self._format_number(self.repo.likes)}")
        stats_layout.addWidget(likes_label)
        
        if self.repo.gated:
            gated_label = QLabel("🔒 Gated")
            gated_label.setStyleSheet("color: #f9e2af;")
            stats_layout.addWidget(gated_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Tags (show first 3)
        if self.repo.tags:
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)
            
            for tag in self.repo.tags[:3]:
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    background-color: #45475a;
                    color: #cdd6f4;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                """)
                tags_layout.addWidget(tag_label)
            
            if len(self.repo.tags) > 3:
                more_label = QLabel(f"+{len(self.repo.tags) - 3}")
                more_label.setObjectName("subtitle")
                tags_layout.addWidget(more_label)
            
            tags_layout.addStretch()
            layout.addLayout(tags_layout)
        
        layout.addStretch()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        view_btn = QPushButton("View")
        view_btn.clicked.connect(self._on_view_clicked)
        buttons_layout.addWidget(view_btn)
        
        buttons_layout.addStretch()
        
        download_btn = QPushButton("⬇️ Download")
        download_btn.setObjectName("primaryButton")
        download_btn.clicked.connect(self._on_download_clicked)
        buttons_layout.addWidget(download_btn)
        
        layout.addLayout(buttons_layout)
    
    def _get_platform_emoji(self) -> str:
        """Get emoji for platform."""
        emojis = {
            "huggingface": "🤗",
            "modelscope": "📦",
            "civitai": "🎨",
        }
        return emojis.get(self.repo.platform, "📥")
    
    def _format_number(self, num: int) -> str:
        """Format large numbers with K/M suffix."""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return str(num)
    
    def _on_view_clicked(self) -> None:
        """Handle view button click - uses internal browser via signal."""
        # Emit signal - parent widget handles navigation in embedded browser
        # No external browser redirects - everything stays in-app
        self.view_clicked.emit(self.repo.repo_id)
    
    def _on_download_clicked(self) -> None:
        """Handle download button click."""
        self.download_clicked.emit(self.repo.repo_id)
