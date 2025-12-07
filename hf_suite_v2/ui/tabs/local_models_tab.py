"""
Local Models tab - Scan and manage locally downloaded models.
"""

import logging
import os
import hashlib
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QScrollArea, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QFileDialog, QProgressBar,
    QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ...core import get_config, get_db, EventBus, Events
from ...core.constants import FILE_CATEGORIES
from ...core.database import LocalModelTable

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """Background worker for scanning directories."""
    
    progress = pyqtSignal(str, int, int)  # current_file, current, total
    model_found = pyqtSignal(dict)
    completed = pyqtSignal(int)  # total found
    error = pyqtSignal(str)
    
    # Common model extensions
    MODEL_EXTENSIONS = {
        '.safetensors', '.ckpt', '.pt', '.pth', '.bin',
        '.gguf', '.ggml', '.q4_0', '.q4_1', '.q5_0', '.q5_1', '.q8_0',
    }
    
    def __init__(self, paths: List[str], compute_hash: bool = False):
        super().__init__()
        self.paths = paths
        self.compute_hash = compute_hash
        self._cancelled = False
    
    def run(self):
        try:
            total_found = 0
            all_files = []
            
            # First pass: collect all files
            for path in self.paths:
                if self._cancelled:
                    return
                
                path = Path(path)
                if not path.exists():
                    continue
                
                for file_path in path.rglob("*"):
                    if file_path.suffix.lower() in self.MODEL_EXTENSIONS:
                        all_files.append(file_path)
            
            # Second pass: process files
            for i, file_path in enumerate(all_files):
                if self._cancelled:
                    return
                
                self.progress.emit(str(file_path), i + 1, len(all_files))
                
                model_info = self._process_file(file_path)
                if model_info:
                    self.model_found.emit(model_info)
                    total_found += 1
            
            self.completed.emit(total_found)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def _process_file(self, file_path: Path) -> Optional[Dict]:
        """Process a single model file."""
        try:
            stat = file_path.stat()
            
            model_info = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": stat.st_size,
                "model_type": self._detect_model_type(file_path),
                "scanned_at": datetime.now(),
            }
            
            # Compute hash if requested (slow for large files)
            if self.compute_hash and stat.st_size < 100 * 1024 * 1024:  # < 100MB
                model_info["file_hash"] = self._compute_hash(file_path)
            
            return model_info
            
        except Exception as e:
            logger.warning(f"Error processing {file_path}: {e}")
            return None
    
    def _detect_model_type(self, file_path: Path) -> str:
        """Detect model type from filename/path."""
        path_lower = str(file_path).lower()
        name_lower = file_path.name.lower()
        
        if "lora" in path_lower or "lora" in name_lower:
            return "lora"
        elif "vae" in path_lower or "vae" in name_lower:
            return "vae"
        elif "controlnet" in path_lower or "control" in name_lower:
            return "controlnet"
        elif "embedding" in path_lower or "embed" in name_lower:
            return "embedding"
        elif "upscale" in path_lower or "esrgan" in name_lower:
            return "upscaler"
        elif ".gguf" in name_lower:
            return "gguf"
        else:
            return "checkpoint"
    
    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of first 1MB."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Only hash first 1MB for speed
            sha256.update(f.read(1024 * 1024))
        return sha256.hexdigest()[:16]
    
    def cancel(self):
        self._cancelled = True


class LocalModelsTab(QWidget):
    """
    Local models management tab.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │  ┌─ Scan Paths ───────────────────────────────────────┐ │
    │  │ [Path 1] [Path 2] [+ Add Path] [🔄 Scan Now]       │ │
    │  └────────────────────────────────────────────────────┘ │
    │                                                         │
    │  ┌─ Filters ──────────────────────────────────────────┐ │
    │  │ [Search...] Type: [All ▾] Sort: [Size ▾]           │ │
    │  └────────────────────────────────────────────────────┘ │
    │                                                         │
    │  [Progress: Scanning... 45/120]                         │
    │                                                         │
    │  ┌─ Models Tree ──────────────────────────────────────┐ │
    │  │ 📁 Checkpoints (45 files, 120 GB)                  │ │
    │  │   └─ sd_xl_base_1.0.safetensors       6.9 GB       │ │
    │  │   └─ v1-5-pruned-emaonly.safetensors  4.3 GB       │ │
    │  │ 📁 LoRA (23 files, 2.3 GB)                         │ │
    │  │   └─ my_lora.safetensors              145 MB       │ │
    │  │ 📁 VAE (5 files, 800 MB)                           │ │
    │  └────────────────────────────────────────────────────┘ │
    │                                                         │
    │  Selected: model.safetensors    [📁 Open] [🗑️ Delete] │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.db = get_db()
        self.event_bus = EventBus()
        self._scan_worker: Optional[ScanWorker] = None
        self._scan_paths: List[str] = []
        
        self._setup_ui()
        self._load_scan_paths()
        self._load_models()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Scan paths section
        layout.addWidget(self._create_scan_section())
        
        # Filters section
        layout.addWidget(self._create_filters_section())
        
        # Progress bar
        self.progress_frame = QFrame()
        progress_layout = QHBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_label = QLabel("Ready to scan")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        progress_layout.addWidget(self.progress_bar)
        
        progress_layout.addStretch()
        self.progress_frame.hide()
        layout.addWidget(self.progress_frame)
        
        # Models tree
        layout.addWidget(self._create_tree(), 1)
        
        # Actions bar
        layout.addWidget(self._create_actions_bar())
    
    def _create_scan_section(self) -> QFrame:
        """Create scan paths section."""
        frame = QFrame()
        frame.setObjectName("card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        layout.addWidget(QLabel("Scan paths:"))
        
        # Path display
        self.paths_label = QLabel("No paths configured")
        self.paths_label.setObjectName("subtitle")
        layout.addWidget(self.paths_label, 1)
        
        # Add path button
        add_path_btn = QPushButton("+ Add Path")
        add_path_btn.clicked.connect(self._add_scan_path)
        layout.addWidget(add_path_btn)
        
        # Auto-detect button
        detect_btn = QPushButton("🔍 Auto-detect")
        detect_btn.clicked.connect(self._auto_detect_paths)
        layout.addWidget(detect_btn)
        
        # Scan button
        self.scan_btn = QPushButton("🔄 Scan Now")
        self.scan_btn.setObjectName("primaryButton")
        self.scan_btn.clicked.connect(self._start_scan)
        layout.addWidget(self.scan_btn)
        
        return frame
    
    def _create_filters_section(self) -> QFrame:
        """Create filters section."""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search models...")
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
        
        # Sort
        layout.addWidget(QLabel("Sort:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Size", "Date"])
        self.sort_combo.setFixedWidth(100)
        layout.addWidget(self.sort_combo)
        
        return frame
    
    def _create_tree(self) -> QTreeWidget:
        """Create the models tree widget."""
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Size", "Type", "Path"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        
        # Column widths
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 100)
        
        return self.tree
    
    def _create_actions_bar(self) -> QWidget:
        """Create the actions bar."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stats_label = QLabel("0 models found")
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
        # Find duplicates
        dup_btn = QPushButton("🔍 Find Duplicates")
        dup_btn.clicked.connect(self._find_duplicates)
        layout.addWidget(dup_btn)
        
        # Open folder
        open_btn = QPushButton("📁 Open Location")
        open_btn.clicked.connect(self._open_selected_location)
        layout.addWidget(open_btn)
        
        # Delete
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self._delete_selected)
        layout.addWidget(delete_btn)
        
        return widget
    
    def _load_scan_paths(self) -> None:
        """Load saved scan paths."""
        # Get from config
        paths = []
        
        if self.config.paths.comfy_root:
            paths.append(self.config.paths.comfy_root)
        if self.config.paths.default_save_path:
            paths.append(self.config.paths.default_save_path)
        
        self._scan_paths = paths
        self._update_paths_display()
    
    def _update_paths_display(self) -> None:
        """Update the paths display label."""
        if self._scan_paths:
            display = ", ".join([os.path.basename(p) or p for p in self._scan_paths[:3]])
            if len(self._scan_paths) > 3:
                display += f" (+{len(self._scan_paths) - 3} more)"
            self.paths_label.setText(display)
        else:
            self.paths_label.setText("No paths configured")
    
    def _add_scan_path(self) -> None:
        """Add a new scan path."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            os.path.expanduser("~")
        )
        if path and path not in self._scan_paths:
            self._scan_paths.append(path)
            self._update_paths_display()
    
    def _auto_detect_paths(self) -> None:
        """Auto-detect common model paths."""
        import platform
        
        # Build platform-agnostic paths
        home = os.path.expanduser("~")
        common_paths = [
            os.path.join(home, ".cache", "huggingface", "hub"),
            os.path.join(home, ".ollama", "models"),
            os.path.join(home, ".lmstudio", "models"),
        ]
        
        # Add Windows-specific paths
        if platform.system() == "Windows":
            localappdata = os.environ.get("LOCALAPPDATA", "")
            if localappdata:
                common_paths.append(os.path.join(localappdata, "lm-studio", "models"))
        
        found = 0
        for path in common_paths:
            if os.path.exists(path) and path not in self._scan_paths:
                self._scan_paths.append(path)
                found += 1
        
        self._update_paths_display()
        self.event_bus.emit(Events.NOTIFICATION, f"Found {found} model directories", "success")
    
    def _start_scan(self) -> None:
        """Start scanning for models."""
        if not self._scan_paths:
            self.event_bus.emit(Events.NOTIFICATION, "No paths to scan", "warning")
            return
        
        self.progress_frame.show()
        self.progress_bar.setValue(0)
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Scanning...")
        
        self._scan_worker = ScanWorker(self._scan_paths, compute_hash=False)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.model_found.connect(self._on_model_found)
        self._scan_worker.completed.connect(self._on_scan_completed)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()
    
    def _on_scan_progress(self, current_file: str, current: int, total: int) -> None:
        """Handle scan progress."""
        self.progress_label.setText(f"Scanning: {os.path.basename(current_file)}")
        self.progress_bar.setValue(int((current / total) * 100))
    
    def _on_model_found(self, model_info: Dict) -> None:
        """Handle model found during scan."""
        self.db.add_local_model(model_info)
    
    def _on_scan_completed(self, total: int) -> None:
        """Handle scan completion."""
        self.progress_frame.hide()
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔄 Scan Now")
        
        self._load_models()
        self.event_bus.emit(Events.SCAN_COMPLETED, total=total)
        self.event_bus.emit(Events.NOTIFICATION, f"Scan complete: {total} models found", "success")
    
    def _on_scan_error(self, error: str) -> None:
        """Handle scan error."""
        self.progress_frame.hide()
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔄 Scan Now")
        self.event_bus.emit(Events.NOTIFICATION, f"Scan failed: {error}", "error")
    
    def _load_models(self) -> None:
        """Load models from database into tree."""
        self.tree.clear()
        
        models = self.db.get_local_models()
        
        # Group by type
        by_type: Dict[str, List] = {}
        total_size = 0
        
        for model in models:
            model_type = model.model_type or "other"
            if model_type not in by_type:
                by_type[model_type] = []
            by_type[model_type].append(model)
            total_size += model.file_size or 0
        
        # Create tree items
        for model_type, type_models in sorted(by_type.items()):
            type_size = sum(m.file_size or 0 for m in type_models)
            
            type_item = QTreeWidgetItem([
                f"📁 {model_type.title()} ({len(type_models)} files)",
                self._format_bytes(type_size),
                "",
                ""
            ])
            type_item.setExpanded(True)
            
            for model in sorted(type_models, key=lambda m: m.file_name):
                model_item = QTreeWidgetItem([
                    model.file_name,
                    self._format_bytes(model.file_size) if model.file_size else "-",
                    model.model_type or "-",
                    model.file_path
                ])
                model_item.setData(0, Qt.ItemDataRole.UserRole, model.file_path)
                type_item.addChild(model_item)
            
            self.tree.addTopLevelItem(type_item)
        
        self.stats_label.setText(f"{len(models)} models, {self._format_bytes(total_size)} total")
    
    def _filter_tree(self) -> None:
        """Filter tree based on search and type."""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentData()
        
        for i in range(self.tree.topLevelItemCount()):
            type_item = self.tree.topLevelItem(i)
            visible_children = 0
            
            for j in range(type_item.childCount()):
                child = type_item.child(j)
                show = True
                
                # Search filter
                if search_text:
                    name = child.text(0).lower()
                    path = child.text(3).lower()
                    if search_text not in name and search_text not in path:
                        show = False
                
                # Type filter
                if type_filter != "all":
                    child_type = child.text(2).lower()
                    if type_filter not in child_type:
                        show = False
                
                child.setHidden(not show)
                if show:
                    visible_children += 1
            
            # Hide empty type groups
            type_item.setHidden(visible_children == 0)
    
    def _find_duplicates(self) -> None:
        """Find duplicate models."""
        duplicates = self.db.find_duplicates()
        
        if not duplicates:
            self.event_bus.emit(Events.NOTIFICATION, "No duplicates found", "info")
            return
        
        # Show duplicates dialog or highlight in tree
        total_dupes = sum(len(models) - 1 for _, models in duplicates)
        self.event_bus.emit(Events.NOTIFICATION, f"Found {total_dupes} duplicate files", "warning")
    
    def _open_selected_location(self) -> None:
        """Open folder for selected model."""
        selected = self.tree.selectedItems()
        if not selected:
            return
        
        item = selected[0]
        path = item.data(0, Qt.ItemDataRole.UserRole)
        
        if path and os.path.exists(path):
            import subprocess
            import platform
            folder = os.path.dirname(path)
            system = platform.system()
            if system == "Windows":
                os.startfile(folder)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", folder])
            else:  # Linux and others
                subprocess.Popen(["xdg-open", folder])
    
    def _delete_selected(self) -> None:
        """Delete selected models."""
        selected = self.tree.selectedItems()
        if not selected:
            return
        
        paths = [item.data(0, Qt.ItemDataRole.UserRole) for item in selected if item.data(0, Qt.ItemDataRole.UserRole)]
        
        if not paths:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Models",
            f"Are you sure you want to delete {len(paths)} model(s)?\nThis cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted = 0
            for path in paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        deleted += 1
                except Exception as e:
                    logger.error(f"Failed to delete {path}: {e}")
            
            self._load_models()
            self.event_bus.emit(Events.NOTIFICATION, f"Deleted {deleted} models", "success")
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes as human-readable."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"
