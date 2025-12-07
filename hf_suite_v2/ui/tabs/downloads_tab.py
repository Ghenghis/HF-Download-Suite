"""
Downloads tab - Main download queue management.
"""

import logging
import os
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QScrollArea, QFileDialog, QSizePolicy, QSpacerItem,
    QDialog, QTextEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...core import get_config, EventBus, Events
from ...core.download import get_download_manager
from ...core.models import ProgressInfo
from ...core.constants import PLATFORMS
from ..widgets.download_card import DownloadCard
from ..dialogs.file_selection_dialog import FileSelectionDialog

logger = logging.getLogger(__name__)


class DownloadsTab(QWidget):
    """
    Downloads tab with queue management.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │  ┌─ Add New Download ─────────────────────────────────┐ │
    │  │ [🤗|📦] [repo/model-id................] [📁] [Add] │ │
    │  └────────────────────────────────────────────────────┘ │
    │                                                         │
    │  Active Downloads (2)                      [Pause All]  │
    │  ┌──────────────────────────────────────────────────┐  │
    │  │ [Download Card 1]                                 │  │
    │  │ [Download Card 2]                                 │  │
    │  └──────────────────────────────────────────────────┘  │
    │                                                         │
    │  Queued (5)                               [Clear Queue] │
    │  ┌──────────────────────────────────────────────────┐  │
    │  │ [Download Card 3]                                 │  │
    │  │ [Download Card 4]                                 │  │
    │  │ ...                                               │  │
    │  └──────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.manager = get_download_manager()
        self.event_bus = EventBus()
        
        self._download_cards = {}  # task_id -> DownloadCard
        self._pending_selected_files = None  # Files selected from dialog
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Add new download section
        layout.addWidget(self._create_add_section())
        
        # Active downloads section
        active_header = self._create_section_header(
            "Active Downloads",
            [("Pause All", self._pause_all)]
        )
        layout.addWidget(active_header)
        
        self.active_scroll = self._create_scroll_area()
        self.active_container = QWidget()
        self.active_layout = QVBoxLayout(self.active_container)
        self.active_layout.setContentsMargins(0, 0, 0, 0)
        self.active_layout.setSpacing(8)
        self.active_layout.addStretch()
        self.active_scroll.setWidget(self.active_container)
        layout.addWidget(self.active_scroll, 1)
        
        # Queued section
        queue_header = self._create_section_header(
            "Queued",
            [("Clear Queue", self._clear_queue)]
        )
        layout.addWidget(queue_header)
        
        self.queue_scroll = self._create_scroll_area()
        self.queue_container = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_layout.setSpacing(8)
        self.queue_layout.addStretch()
        self.queue_scroll.setWidget(self.queue_container)
        layout.addWidget(self.queue_scroll, 1)
    
    def _create_add_section(self) -> QFrame:
        """Create the add new download section."""
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
        
        # Type selector
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Model", "Dataset"])
        self.type_combo.setFixedWidth(100)
        layout.addWidget(self.type_combo)
        
        # Repo ID input
        self.repo_input = QLineEdit()
        self.repo_input.setPlaceholderText("Enter repository ID (e.g., username/model-name)")
        self.repo_input.returnPressed.connect(self._add_download)
        layout.addWidget(self.repo_input, 1)
        
        # Path selector
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Save path...")
        self.path_input.setText(self.config.paths.default_save_path)
        self.path_input.setFixedWidth(200)
        layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("📁")
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self._browse_path)
        layout.addWidget(browse_btn)
        
        # Select files button
        self.select_files_btn = QPushButton("📋 Select Files")
        self.select_files_btn.setFixedWidth(100)
        self.select_files_btn.setToolTip("Choose specific files to download")
        self.select_files_btn.clicked.connect(self._show_file_selection)
        layout.addWidget(self.select_files_btn)
        
        # Add button
        self.add_btn = QPushButton("Add to Queue")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setFixedWidth(120)
        self.add_btn.clicked.connect(self._add_download)
        layout.addWidget(self.add_btn)
        
        # Batch import button
        self.batch_btn = QPushButton("📋 Batch")
        self.batch_btn.setFixedWidth(80)
        self.batch_btn.setToolTip("Import multiple repositories at once")
        self.batch_btn.clicked.connect(self._show_batch_dialog)
        layout.addWidget(self.batch_btn)
        
        return frame
    
    def _create_section_header(self, title: str, buttons: list) -> QWidget:
        """Create a section header with optional buttons."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 4)
        
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        
        self._section_counts = getattr(self, '_section_counts', {})
        count_label = QLabel("(0)")
        count_label.setObjectName("subtitle")
        self._section_counts[title] = count_label
        layout.addWidget(count_label)
        
        layout.addStretch()
        
        for btn_text, btn_callback in buttons:
            btn = QPushButton(btn_text)
            btn.clicked.connect(btn_callback)
            layout.addWidget(btn)
        
        return widget
    
    def _create_scroll_area(self) -> QScrollArea:
        """Create a styled scroll area."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Manager signals
        self.manager.task_started.connect(self._on_task_started)
        self.manager.task_progress.connect(self._on_task_progress)
        self.manager.task_completed.connect(self._on_task_completed)
        self.manager.task_failed.connect(self._on_task_failed)
        self.manager.task_cancelled.connect(self._on_task_cancelled)
        self.manager.queue_changed.connect(self._refresh_queue)
    
    def _show_file_selection(self) -> None:
        """Show the file selection dialog."""
        repo_id = self.repo_input.text().strip()
        if not repo_id:
            self.event_bus.emit(Events.NOTIFICATION, "Please enter a repository ID first", "warning")
            return
        
        platform = self.platform_combo.currentData()
        repo_type = self.type_combo.currentText().lower()
        
        dialog = FileSelectionDialog(
            repo_id=repo_id,
            platform=platform,
            repo_type=repo_type,
            parent=self
        )
        dialog.files_selected.connect(self._on_files_selected)
        dialog.exec()
    
    def _on_files_selected(self, files: list) -> None:
        """Handle files selected from dialog."""
        self._pending_selected_files = files
        file_count = len(files)
        self.event_bus.emit(
            Events.NOTIFICATION,
            f"Selected {file_count} files. Click 'Add to Queue' to download.",
            "info"
        )
        # Update button to show files are selected
        self.add_btn.setText(f"Add ({file_count} files)")
    
    def _add_download(self) -> None:
        """Add a new download to the queue."""
        repo_id = self.repo_input.text().strip()
        if not repo_id:
            self.event_bus.emit(Events.NOTIFICATION, "Please enter a repository ID", "warning")
            return
        
        save_path = self.path_input.text().strip()
        if not save_path:
            self.event_bus.emit(Events.NOTIFICATION, "Please select a save path", "warning")
            return
        
        platform = self.platform_combo.currentData()
        repo_type = self.type_combo.currentText().lower()
        
        # Get selected files (if any)
        selected_files = self._pending_selected_files
        
        try:
            task_id = self.manager.add(
                repo_id=repo_id,
                save_path=save_path,
                platform=platform,
                repo_type=repo_type,
                selected_files=selected_files,
            )
            
            # Clear input and reset state
            self.repo_input.clear()
            self._pending_selected_files = None
            self.add_btn.setText("Add to Queue")
            
            # Save path for next time
            self.config.update(**{"paths.default_save_path": save_path})
            self.config.add_recent_repo(repo_id)
            
            files_msg = f" ({len(selected_files)} files)" if selected_files else ""
            self.event_bus.emit(Events.NOTIFICATION, f"Added {repo_id}{files_msg} to queue", "success")
            logger.info(f"Added download: {repo_id}")
            
        except Exception as e:
            self.event_bus.emit(Events.NOTIFICATION, f"Failed to add: {e}", "error")
            logger.error(f"Failed to add download: {e}")
    
    def _browse_path(self) -> None:
        """Browse for save path."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Save Directory",
            self.path_input.text() or os.path.expanduser("~")
        )
        if path:
            self.path_input.setText(path)
    
    def _pause_all(self) -> None:
        """Pause all active downloads."""
        for task_id in list(self._download_cards.keys()):
            self.manager.pause(task_id)
    
    def _clear_queue(self) -> None:
        """Clear the download queue."""
        # Implementation depends on manager methods
        pass
    
    def _on_task_started(self, task_id: int) -> None:
        """Handle task started."""
        tasks = self.manager.get_active_downloads()
        for task in tasks:
            if task.id == task_id:
                card = DownloadCard(task)
                card.pause_clicked.connect(lambda tid=task_id: self.manager.pause(tid))
                card.cancel_clicked.connect(lambda tid=task_id: self.manager.cancel(tid))
                
                self._download_cards[task_id] = card
                # Insert before the stretch
                self.active_layout.insertWidget(self.active_layout.count() - 1, card)
                break
        
        self._update_counts()
    
    def _on_task_progress(self, progress: ProgressInfo) -> None:
        """Handle task progress update."""
        card = self._download_cards.get(progress.task_id)
        if card:
            card.update_progress(progress)
    
    def _on_task_completed(self, task_id: int, path: str) -> None:
        """Handle task completion."""
        self._remove_card(task_id)
        self._update_counts()
    
    def _on_task_failed(self, task_id: int, error: str) -> None:
        """Handle task failure."""
        card = self._download_cards.get(task_id)
        if card:
            card.set_error(error)
    
    def _on_task_cancelled(self, task_id: int) -> None:
        """Handle task cancellation."""
        self._remove_card(task_id)
        self._update_counts()
    
    def _remove_card(self, task_id: int) -> None:
        """Remove a download card."""
        card = self._download_cards.pop(task_id, None)
        if card:
            card.setParent(None)
            card.deleteLater()
    
    def _refresh_queue(self) -> None:
        """Refresh the queue display."""
        self._update_counts()
    
    def _update_counts(self) -> None:
        """Update section count labels."""
        status = self.manager.get_status()
        
        if "Active Downloads" in self._section_counts:
            self._section_counts["Active Downloads"].setText(f"({status['active_count']})")
        
        if "Queued" in self._section_counts:
            self._section_counts["Queued"].setText(f"({status['queue_size']})")
    
    def _show_batch_dialog(self) -> None:
        """Show batch import dialog."""
        dialog = BatchImportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            repos = dialog.get_repos()
            if repos:
                self._add_batch_downloads(repos)
    
    def _add_batch_downloads(self, repo_ids: list) -> None:
        """Add multiple downloads from list of repo IDs."""
        platform = self.platform_combo.currentData()
        repo_type = "model" if self.type_combo.currentText() == "Model" else "dataset"
        save_path = self.path_input.text() or self.config.paths.default_save_path
        
        added_count = 0
        for repo_id in repo_ids:
            repo_id = repo_id.strip()
            if not repo_id or repo_id.startswith('#'):  # Skip empty lines and comments
                continue
            
            try:
                self.manager.add(
                    repo_id=repo_id,
                    platform=platform,
                    repo_type=repo_type,
                    save_path=save_path,
                )
                added_count += 1
            except Exception as e:
                logger.warning(f"Failed to add {repo_id}: {e}")
        
        if added_count > 0:
            self.event_bus.emit(Events.NOTIFICATION, f"Added {added_count} downloads to queue", "success")
            self.config.add_recent_repo(repo_ids[0] if repo_ids else "")  # Add first as recent
        
        self._update_counts()


class BatchImportDialog(QDialog):
    """Dialog for batch importing multiple repository IDs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Import")
        self.setMinimumSize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Instructions
        instructions = QLabel(
            "Enter repository IDs, one per line.\n"
            "Lines starting with # are treated as comments.\n\n"
            "Examples:\n"
            "  TheBloke/Llama-2-7B-GGUF\n"
            "  stabilityai/stable-diffusion-xl-base-1.0\n"
            "  # This is a comment"
        )
        instructions.setObjectName("subtitle")
        layout.addWidget(instructions)
        
        # Text input
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter repository IDs here...")
        layout.addWidget(self.text_edit, 1)
        
        # Count label
        self.count_label = QLabel("0 repositories")
        self.text_edit.textChanged.connect(self._update_count)
        layout.addWidget(self.count_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _update_count(self) -> None:
        """Update the repository count."""
        repos = self.get_repos()
        count = len(repos)
        self.count_label.setText(f"{count} repositor{'y' if count == 1 else 'ies'}")
    
    def get_repos(self) -> list:
        """Get list of valid repository IDs from input."""
        text = self.text_edit.toPlainText()
        lines = text.strip().split('\n')
        
        repos = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Basic validation: should contain '/'
                if '/' in line:
                    repos.append(line)
        
        return repos
