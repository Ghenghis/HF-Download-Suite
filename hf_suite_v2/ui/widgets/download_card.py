"""
Download card widget - Visual representation of a download task.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...core.models import DownloadTask, ProgressInfo, DownloadStatus
from ...core.constants import PLATFORMS

logger = logging.getLogger(__name__)


class DownloadCard(QFrame):
    """
    Visual card representing a download task.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ [🤗] model-name                           [⏸️] [❌]     │
    │ username/repo-id                                        │
    │ ████████████░░░░░░░░░░  45.2% | 1.2 GB / 2.7 GB        │
    │ ⬇️ 12.5 MB/s | ⏱️ 2m 15s remaining                      │
    └─────────────────────────────────────────────────────────┘
    """
    
    pause_clicked = pyqtSignal(int)  # task_id
    resume_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    retry_clicked = pyqtSignal(int)
    
    def __init__(self, task: DownloadTask):
        super().__init__()
        
        self.task = task
        self._is_paused = False
        
        self.setObjectName("card")
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self._setup_ui()
        self._update_display()
    
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Top row: icon, name, buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        # Platform icon
        platform_info = PLATFORMS.get(self.task.platform, PLATFORMS["huggingface"])
        self.icon_label = QLabel(self._get_platform_emoji())
        self.icon_label.setFixedSize(24, 24)
        top_row.addWidget(self.icon_label)
        
        # Model name
        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)
        
        self.name_label = QLabel(self.task.repo_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        name_layout.addWidget(self.name_label)
        
        self.repo_label = QLabel(self.task.repo_id)
        self.repo_label.setObjectName("subtitle")
        name_layout.addWidget(self.repo_label)
        
        top_row.addLayout(name_layout, 1)
        
        # Action buttons
        self.pause_btn = QPushButton("⏸️")
        self.pause_btn.setFixedSize(32, 32)
        self.pause_btn.setToolTip("Pause")
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        top_row.addWidget(self.pause_btn)
        
        self.cancel_btn = QPushButton("❌")
        self.cancel_btn.setFixedSize(32, 32)
        self.cancel_btn.setToolTip("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        top_row.addWidget(self.cancel_btn)
        
        layout.addLayout(top_row)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)
        
        # Progress info row
        info_row = QHBoxLayout()
        
        self.progress_label = QLabel("0% | 0 B / 0 B")
        info_row.addWidget(self.progress_label)
        
        info_row.addStretch()
        
        self.speed_label = QLabel("⬇️ 0 B/s")
        info_row.addWidget(self.speed_label)
        
        self.eta_label = QLabel("⏱️ --")
        info_row.addWidget(self.eta_label)
        
        layout.addLayout(info_row)
        
        # Error message (hidden by default)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #f38ba8;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
    
    def _get_platform_emoji(self) -> str:
        """Get emoji for platform."""
        emojis = {
            "huggingface": "🤗",
            "modelscope": "📦",
            "civitai": "🎨",
        }
        return emojis.get(self.task.platform, "📥")
    
    def _update_display(self) -> None:
        """Update display based on task state."""
        # Update button states based on status
        if self.task.status == DownloadStatus.PAUSED:
            self.pause_btn.setText("▶️")
            self.pause_btn.setToolTip("Resume")
            self._is_paused = True
        else:
            self.pause_btn.setText("⏸️")
            self.pause_btn.setToolTip("Pause")
            self._is_paused = False
        
        if self.task.status == DownloadStatus.FAILED:
            self.pause_btn.setText("🔄")
            self.pause_btn.setToolTip("Retry")
    
    def update_progress(self, progress: ProgressInfo) -> None:
        """Update progress display."""
        # Update progress bar
        percent = int(progress.progress_percent)
        self.progress_bar.setValue(percent)
        
        # Update labels
        downloaded = self._format_bytes(progress.downloaded_bytes)
        total = self._format_bytes(progress.total_bytes)
        self.progress_label.setText(f"{percent}% | {downloaded} / {total}")
        
        self.speed_label.setText(f"⬇️ {progress.speed_formatted}")
        self.eta_label.setText(f"⏱️ {progress.eta_formatted}")
    
    def set_error(self, error: str) -> None:
        """Display an error message."""
        self.error_label.setText(f"❌ {error}")
        self.error_label.show()
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #f38ba8; }")
        self.pause_btn.setText("🔄")
        self.pause_btn.setToolTip("Retry")
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"
    
    def _on_pause_clicked(self) -> None:
        """Handle pause/resume button click."""
        if self.task.status == DownloadStatus.FAILED:
            self.retry_clicked.emit(self.task.id)
        elif self._is_paused:
            self.resume_clicked.emit(self.task.id)
            self._is_paused = False
            self.pause_btn.setText("⏸️")
            self.pause_btn.setToolTip("Pause")
        else:
            self.pause_clicked.emit(self.task.id)
            self._is_paused = True
            self.pause_btn.setText("▶️")
            self.pause_btn.setToolTip("Resume")
    
    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.cancel_clicked.emit(self.task.id)
