"""
File selection dialog - Browse and select files from a repository.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QTreeWidget, QTreeWidgetItem, QHeaderView,
    QProgressBar, QDialogButtonBox, QGroupBox,
    QComboBox, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ...core import get_config
from ...core.constants import FILE_CATEGORIES

logger = logging.getLogger(__name__)


@dataclass
class RepoFile:
    """Represents a file in a repository."""
    path: str
    size: int
    blob_id: Optional[str] = None
    lfs: bool = False


class FetchFilesWorker(QThread):
    """Background worker to fetch repository file list."""
    
    files_ready = pyqtSignal(list)  # List[RepoFile]
    error = pyqtSignal(str)
    
    def __init__(self, repo_id: str, platform: str, repo_type: str):
        super().__init__()
        self.repo_id = repo_id
        self.platform = platform
        self.repo_type = repo_type
    
    def run(self):
        try:
            files = self._fetch_files()
            self.files_ready.emit(files)
        except Exception as e:
            self.error.emit(str(e))
    
    def _fetch_files(self) -> List[RepoFile]:
        """Fetch file list from the repository."""
        files = []
        
        if self.platform == "huggingface":
            from huggingface_hub import HfApi
            
            api = HfApi()
            
            try:
                if self.repo_type == "model":
                    repo_info = api.model_info(self.repo_id, files_metadata=True)
                else:
                    repo_info = api.dataset_info(self.repo_id, files_metadata=True)
                
                if repo_info.siblings:
                    for sibling in repo_info.siblings:
                        files.append(RepoFile(
                            path=sibling.rfilename,
                            size=sibling.size or 0,
                            blob_id=sibling.blob_id,
                            lfs=sibling.lfs is not None if hasattr(sibling, 'lfs') else False,
                        ))
                        
            except Exception as e:
                logger.error(f"Failed to fetch HF files: {e}")
                raise
        
        elif self.platform == "modelscope":
            # ModelScope API for file listing
            try:
                from modelscope.hub.api import HubApi
                
                api = HubApi()
                file_list = api.get_model_files(self.repo_id)
                
                for file_info in file_list:
                    files.append(RepoFile(
                        path=file_info.get("Path", file_info.get("name", "")),
                        size=file_info.get("Size", 0),
                    ))
                    
            except Exception as e:
                logger.error(f"Failed to fetch ModelScope files: {e}")
                raise
        
        return sorted(files, key=lambda f: f.path)


class FileSelectionDialog(QDialog):
    """
    Dialog for selecting specific files from a repository.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │  Select Files to Download                    [×]        │
    ├─────────────────────────────────────────────────────────┤
    │  Repository: stabilityai/stable-diffusion-xl-base-1.0   │
    │                                                         │
    │  ┌─ Filters ──────────────────────────────────────────┐ │
    │  │ [Search...] Type: [All ▾] [☑ Select All]           │ │
    │  └────────────────────────────────────────────────────┘ │
    │                                                         │
    │  ┌─ Files ────────────────────────────────────────────┐ │
    │  │ ☑ │ File Name              │ Size    │ Type        │ │
    │  │───┼────────────────────────┼─────────┼─────────────│ │
    │  │ ☑ │ model.safetensors      │ 6.9 GB  │ Checkpoint  │ │
    │  │ ☑ │ vae/diffusion_pytorch  │ 335 MB  │ VAE         │ │
    │  │ ☐ │ model.onnx             │ 6.9 GB  │ ONNX        │ │
    │  │ ☐ │ README.md              │ 12 KB   │ Text        │ │
    │  └────────────────────────────────────────────────────┘ │
    │                                                         │
    │  Selected: 2 files (7.2 GB)                             │
    │                                                         │
    │  [Recommend Best Files]     [Cancel]  [Download Selected]│
    └─────────────────────────────────────────────────────────┘
    """
    
    # Signal emitted with list of selected file paths
    files_selected = pyqtSignal(list)
    
    def __init__(
        self,
        repo_id: str,
        platform: str = "huggingface",
        repo_type: str = "model",
        parent=None
    ):
        super().__init__(parent)
        
        self.repo_id = repo_id
        self.platform = platform
        self.repo_type = repo_type
        self.config = get_config()
        
        self._files: List[RepoFile] = []
        self._fetch_worker: Optional[FetchFilesWorker] = None
        
        self._setup_ui()
        self._start_fetch()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Select Files to Download")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Repository info
        repo_frame = QFrame()
        repo_frame.setObjectName("card")
        repo_layout = QHBoxLayout(repo_frame)
        
        repo_layout.addWidget(QLabel("Repository:"))
        repo_label = QLabel(f"<b>{self.repo_id}</b>")
        repo_layout.addWidget(repo_label, 1)
        
        platform_label = QLabel(f"Platform: {self.platform.title()}")
        platform_label.setObjectName("subtitle")
        repo_layout.addWidget(platform_label)
        
        layout.addWidget(repo_frame)
        
        # Filters
        layout.addWidget(self._create_filters())
        
        # Loading indicator
        self.loading_frame = QFrame()
        loading_layout = QVBoxLayout(self.loading_frame)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.loading_label = QLabel("Fetching file list...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.loading_label)
        
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)  # Indeterminate
        self.loading_progress.setFixedWidth(200)
        loading_layout.addWidget(self.loading_progress, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.loading_frame)
        
        # File tree
        self.tree = self._create_tree()
        self.tree.hide()
        layout.addWidget(self.tree, 1)
        
        # Selection summary
        self.summary_label = QLabel("Selected: 0 files (0 B)")
        layout.addWidget(self.summary_label)
        
        # Buttons
        layout.addWidget(self._create_buttons())
    
    def _create_filters(self) -> QFrame:
        """Create the filters section."""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.textChanged.connect(self._filter_tree)
        layout.addWidget(self.search_input, 1)
        
        # Type filter
        layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types", "all")
        for key, info in FILE_CATEGORIES.items():
            self.type_filter.addItem(info["label"], key)
        self.type_filter.currentIndexChanged.connect(self._filter_tree)
        self.type_filter.setFixedWidth(150)
        layout.addWidget(self.type_filter)
        
        # Select all checkbox
        self.select_all_check = QCheckBox("Select All")
        self.select_all_check.stateChanged.connect(self._on_select_all)
        layout.addWidget(self.select_all_check)
        
        return frame
    
    def _create_tree(self) -> QTreeWidget:
        """Create the file tree."""
        tree = QTreeWidget()
        tree.setHeaderLabels(["", "File", "Size", "Type"])
        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(False)
        
        # Column widths
        header = tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        tree.setColumnWidth(0, 40)
        tree.setColumnWidth(2, 100)
        tree.setColumnWidth(3, 120)
        
        # Item change signal
        tree.itemChanged.connect(self._update_summary)
        
        return tree
    
    def _create_buttons(self) -> QWidget:
        """Create the button bar."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Recommend button
        recommend_btn = QPushButton("🎯 Recommend Best Files")
        recommend_btn.clicked.connect(self._recommend_files)
        layout.addWidget(recommend_btn)
        
        layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # Download button
        self.download_btn = QPushButton("⬇️ Download Selected")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.clicked.connect(self._on_download)
        self.download_btn.setEnabled(False)
        layout.addWidget(self.download_btn)
        
        return widget
    
    def _start_fetch(self) -> None:
        """Start fetching the file list."""
        self._fetch_worker = FetchFilesWorker(
            self.repo_id,
            self.platform,
            self.repo_type
        )
        self._fetch_worker.files_ready.connect(self._on_files_ready)
        self._fetch_worker.error.connect(self._on_fetch_error)
        self._fetch_worker.start()
    
    def _on_files_ready(self, files: List[RepoFile]) -> None:
        """Handle files fetched successfully."""
        self._files = files
        self.loading_frame.hide()
        self.tree.show()
        
        self._populate_tree()
        self._recommend_files()  # Auto-select recommended files
    
    def _on_fetch_error(self, error: str) -> None:
        """Handle fetch error."""
        self.loading_label.setText(f"Error: {error}")
        self.loading_progress.hide()
    
    def _populate_tree(self) -> None:
        """Populate the tree with files."""
        self.tree.clear()
        
        for file in self._files:
            item = QTreeWidgetItem()
            
            # Checkbox (column 0)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            
            # File name
            item.setText(1, file.path)
            item.setToolTip(1, file.path)
            
            # Size
            item.setText(2, self._format_bytes(file.size))
            item.setData(2, Qt.ItemDataRole.UserRole, file.size)
            
            # Type
            file_type = self._detect_file_type(file.path)
            item.setText(3, file_type)
            
            # Store file data
            item.setData(0, Qt.ItemDataRole.UserRole, file)
            
            self.tree.addTopLevelItem(item)
        
        self._update_summary()
    
    def _detect_file_type(self, path: str) -> str:
        """Detect file type from path."""
        path_lower = path.lower()
        
        for key, info in FILE_CATEGORIES.items():
            for ext in info.get("extensions", []):
                if path_lower.endswith(ext):
                    return info["label"]
        
        # Fallback
        if path_lower.endswith(('.md', '.txt', '.json', '.yaml', '.yml')):
            return "Config"
        elif path_lower.endswith(('.py', '.sh')):
            return "Script"
        
        return "Other"
    
    def _filter_tree(self) -> None:
        """Filter tree based on search and type."""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentData()
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            show = True
            
            # Search filter
            if search_text:
                file_path = item.text(1).lower()
                if search_text not in file_path:
                    show = False
            
            # Type filter
            if type_filter != "all":
                file_type = item.text(3).lower()
                expected = FILE_CATEGORIES.get(type_filter, {}).get("label", "").lower()
                if expected not in file_type:
                    show = False
            
            item.setHidden(not show)
    
    def _on_select_all(self, state: int) -> None:
        """Handle select all checkbox."""
        check_state = Qt.CheckState.Checked if state else Qt.CheckState.Unchecked
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if not item.isHidden():
                item.setCheckState(0, check_state)
    
    def _recommend_files(self) -> None:
        """Auto-select recommended files (safetensors, configs)."""
        recommended_extensions = {'.safetensors', '.json', '.txt'}
        skip_extensions = {'.onnx', '.h5', '.ot', '.msgpack', '.pkl'}
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            file: RepoFile = item.data(0, Qt.ItemDataRole.UserRole)
            
            path_lower = file.path.lower()
            
            # Skip large non-essential files
            should_skip = any(path_lower.endswith(ext) for ext in skip_extensions)
            
            # Include recommended files
            should_include = any(path_lower.endswith(ext) for ext in recommended_extensions)
            
            if should_include and not should_skip:
                item.setCheckState(0, Qt.CheckState.Checked)
            else:
                item.setCheckState(0, Qt.CheckState.Unchecked)
        
        self._update_summary()
    
    def _update_summary(self) -> None:
        """Update the selection summary."""
        selected_count = 0
        selected_size = 0
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                selected_count += 1
                selected_size += item.data(2, Qt.ItemDataRole.UserRole) or 0
        
        self.summary_label.setText(
            f"Selected: {selected_count} files ({self._format_bytes(selected_size)})"
        )
        self.download_btn.setEnabled(selected_count > 0)
    
    def _on_download(self) -> None:
        """Handle download button click."""
        selected_files = []
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                file: RepoFile = item.data(0, Qt.ItemDataRole.UserRole)
                selected_files.append(file.path)
        
        self.files_selected.emit(selected_files)
        self.accept()
    
    def get_selected_files(self) -> List[str]:
        """Get list of selected file paths."""
        selected = []
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                file: RepoFile = item.data(0, Qt.ItemDataRole.UserRole)
                selected.append(file.path)
        
        return selected
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes as human-readable."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"
