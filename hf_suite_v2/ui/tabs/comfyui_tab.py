"""
ComfyUI Integration tab - Parse workflows and download missing models.
"""

import logging
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QComboBox, QCheckBox, QSplitter,
    QFrame, QTextEdit, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QColor

from ...core import get_config, get_database, EventBus, Events
from ...core.download import get_download_manager
from ...core.models import DownloadStatus
from ...integrations.comfyui.parser import ComfyUIWorkflowParser, ModelReference, WorkflowInfo
from ...integrations.comfyui.resolver import ComfyUIModelResolver, ResolvedModel

logger = logging.getLogger(__name__)


class ResolverWorker(QThread):
    """Background worker for resolving models."""
    
    progress = pyqtSignal(int, int)  # current, total
    resolved = pyqtSignal(str, object)  # model_name, ResolvedModel or None
    finished = pyqtSignal()
    
    def __init__(self, models: List[ModelReference]):
        super().__init__()
        self.models = models
        self.resolver = ComfyUIModelResolver(search_hf=True)
        self._cancelled = False
    
    def run(self):
        total = len(self.models)
        for i, model in enumerate(self.models):
            if self._cancelled:
                break
            
            self.progress.emit(i + 1, total)
            result = self.resolver.resolve(model)
            self.resolved.emit(model.name, result)
        
        self.finished.emit()
    
    def cancel(self):
        self._cancelled = True


class ComfyUITab(QWidget):
    """
    ComfyUI Integration tab for parsing workflows and downloading missing models.
    
    Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │  ComfyUI Root: [/path/to/comfyui        ] [Browse] [Detect]     │
    ├─────────────────────────────────────────────────────────────────┤
    │  Workflow File: [                       ] [Browse] [Parse]      │
    ├─────────────────────────────────────────────────────────────────┤
    │  ┌─ Workflow Info ────────────────────────────────────────────┐ │
    │  │ Source: workflow.json | Nodes: 45 | Models: 12            │ │
    │  └────────────────────────────────────────────────────────────┘ │
    │  ┌─ Models ───────────────────────────────────────────────────┐ │
    │  │ [x] | Name          | Type      | Status  | HF Repo        │ │
    │  │ [x] | sd_xl_base... | checkpoint| Missing | stabilityai/...│ │
    │  │ [x] | my_lora.saf...| lora      | Found   | -              │ │
    │  └────────────────────────────────────────────────────────────┘ │
    │  [Select All] [Select Missing] [Resolve Selected] [Download]    │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    download_requested = pyqtSignal(str, str, str)  # repo_id, platform, path
    
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.db = get_database()
        self.event_bus = EventBus()
        self.download_manager = get_download_manager()
        
        self.parser: Optional[ComfyUIWorkflowParser] = None
        self.workflow_info: Optional[WorkflowInfo] = None
        self.resolved_models: dict[str, Optional[ResolvedModel]] = {}
        self.resolver_worker: Optional[ResolverWorker] = None
        
        self._setup_ui()
        self._setup_connections()
        self._load_settings()
        
        logger.info("ComfyUI tab initialized")
    
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # ComfyUI Root section
        layout.addWidget(self._create_comfyui_root_section())
        
        # Workflow file section
        layout.addWidget(self._create_workflow_section())
        
        # Workflow info section
        self.info_group = self._create_info_section()
        layout.addWidget(self.info_group)
        
        # Models table
        layout.addWidget(self._create_models_section(), 1)
        
        # Actions bar
        layout.addWidget(self._create_actions_bar())
    
    def _create_comfyui_root_section(self) -> QGroupBox:
        """Create the ComfyUI root path section."""
        group = QGroupBox("ComfyUI Installation")
        layout = QHBoxLayout(group)
        
        layout.addWidget(QLabel("ComfyUI Root:"))
        
        self.comfy_root_input = QLineEdit()
        self.comfy_root_input.setPlaceholderText("Path to ComfyUI installation (e.g., C:/ComfyUI)")
        layout.addWidget(self.comfy_root_input, 1)
        
        self.browse_comfy_btn = QPushButton("Browse")
        self.browse_comfy_btn.setFixedWidth(80)
        layout.addWidget(self.browse_comfy_btn)
        
        self.detect_comfy_btn = QPushButton("Auto-Detect")
        self.detect_comfy_btn.setFixedWidth(100)
        layout.addWidget(self.detect_comfy_btn)
        
        return group
    
    def _create_workflow_section(self) -> QGroupBox:
        """Create the workflow file selection section."""
        group = QGroupBox("Workflow File")
        layout = QHBoxLayout(group)
        
        self.workflow_input = QLineEdit()
        self.workflow_input.setPlaceholderText("Select a workflow.json or PNG file with embedded workflow")
        layout.addWidget(self.workflow_input, 1)
        
        self.browse_workflow_btn = QPushButton("Browse")
        self.browse_workflow_btn.setFixedWidth(80)
        layout.addWidget(self.browse_workflow_btn)
        
        self.parse_btn = QPushButton("Parse Workflow")
        self.parse_btn.setFixedWidth(120)
        self.parse_btn.setEnabled(False)
        layout.addWidget(self.parse_btn)
        
        return group
    
    def _create_info_section(self) -> QGroupBox:
        """Create the workflow info display section."""
        group = QGroupBox("Workflow Information")
        layout = QHBoxLayout(group)
        
        self.info_source = QLabel("Source: -")
        layout.addWidget(self.info_source)
        
        layout.addWidget(self._create_separator())
        
        self.info_nodes = QLabel("Nodes: -")
        layout.addWidget(self.info_nodes)
        
        layout.addWidget(self._create_separator())
        
        self.info_models = QLabel("Models: -")
        layout.addWidget(self.info_models)
        
        layout.addWidget(self._create_separator())
        
        self.info_missing = QLabel("Missing: -")
        self.info_missing.setStyleSheet("color: #f38ba8;")
        layout.addWidget(self.info_missing)
        
        layout.addStretch()
        
        return group
    
    def _create_models_section(self) -> QGroupBox:
        """Create the models table section."""
        group = QGroupBox("Model References")
        layout = QVBoxLayout(group)
        
        # Progress bar for resolution
        self.resolve_progress = QProgressBar()
        self.resolve_progress.setVisible(False)
        self.resolve_progress.setTextVisible(True)
        layout.addWidget(self.resolve_progress)
        
        # Models table
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(6)
        self.models_table.setHorizontalHeaderLabels([
            "", "Model Name", "Type", "Status", "HuggingFace Repo", "Confidence"
        ])
        
        header = self.models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.models_table.setColumnWidth(0, 30)
        self.models_table.setColumnWidth(2, 100)
        self.models_table.setColumnWidth(3, 80)
        self.models_table.setColumnWidth(5, 80)
        
        self.models_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.models_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.models_table)
        
        return group
    
    def _create_actions_bar(self) -> QWidget:
        """Create the actions toolbar."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setEnabled(False)
        layout.addWidget(self.select_all_btn)
        
        self.select_missing_btn = QPushButton("Select Missing")
        self.select_missing_btn.setEnabled(False)
        layout.addWidget(self.select_missing_btn)
        
        self.deselect_btn = QPushButton("Deselect All")
        self.deselect_btn.setEnabled(False)
        layout.addWidget(self.deselect_btn)
        
        layout.addWidget(self._create_separator())
        
        self.resolve_btn = QPushButton("Resolve to HuggingFace")
        self.resolve_btn.setEnabled(False)
        layout.addWidget(self.resolve_btn)
        
        layout.addStretch()
        
        self.download_btn = QPushButton("Download Selected")
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet("background-color: #89b4fa; color: #1e1e2e; font-weight: bold;")
        layout.addWidget(self.download_btn)
        
        return widget
    
    def _create_separator(self) -> QFrame:
        """Create a vertical separator."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        return sep
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Browse buttons
        self.browse_comfy_btn.clicked.connect(self._browse_comfy_root)
        self.detect_comfy_btn.clicked.connect(self._detect_comfy_root)
        self.browse_workflow_btn.clicked.connect(self._browse_workflow)
        
        # Parse button
        self.parse_btn.clicked.connect(self._parse_workflow)
        self.workflow_input.textChanged.connect(
            lambda t: self.parse_btn.setEnabled(bool(t.strip()))
        )
        
        # Selection buttons
        self.select_all_btn.clicked.connect(self._select_all)
        self.select_missing_btn.clicked.connect(self._select_missing)
        self.deselect_btn.clicked.connect(self._deselect_all)
        
        # Resolve button
        self.resolve_btn.clicked.connect(self._resolve_models)
        
        # Download button
        self.download_btn.clicked.connect(self._download_selected)
        
        # ComfyUI root change
        self.comfy_root_input.textChanged.connect(self._on_comfy_root_changed)
    
    def _load_settings(self) -> None:
        """Load saved settings."""
        comfy_root = self.db.get_setting("comfyui_root", "")
        if comfy_root:
            self.comfy_root_input.setText(comfy_root)
    
    def _browse_comfy_root(self) -> None:
        """Browse for ComfyUI root directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select ComfyUI Root Directory",
            self.comfy_root_input.text() or str(Path.home()),
        )
        if path:
            self.comfy_root_input.setText(path)
    
    def _detect_comfy_root(self) -> None:
        """Auto-detect ComfyUI installation."""
        common_paths = [
            Path.home() / "ComfyUI",
            Path.home() / "comfyui",
            Path("C:/ComfyUI"),
            Path("D:/ComfyUI"),
            Path.home() / "Documents" / "ComfyUI",
            Path.home() / "AI" / "ComfyUI",
        ]
        
        for path in common_paths:
            if path.exists() and (path / "main.py").exists():
                self.comfy_root_input.setText(str(path))
                self.event_bus.emit(Events.NOTIFICATION, f"Found ComfyUI at {path}", "success")
                return
        
        self.event_bus.emit(Events.NOTIFICATION, "ComfyUI installation not found", "warning")
    
    def _on_comfy_root_changed(self, text: str) -> None:
        """Handle ComfyUI root path change."""
        if text:
            self.db.set_setting("comfyui_root", text)
            self.parser = ComfyUIWorkflowParser(text)
        else:
            self.parser = ComfyUIWorkflowParser()
    
    def _browse_workflow(self) -> None:
        """Browse for workflow file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Workflow File",
            str(Path.home()),
            "Workflow Files (*.json *.png);;JSON Files (*.json);;PNG Files (*.png);;All Files (*.*)"
        )
        if path:
            self.workflow_input.setText(path)
    
    def _parse_workflow(self) -> None:
        """Parse the selected workflow file."""
        filepath = self.workflow_input.text().strip()
        if not filepath:
            return
        
        if not self.parser:
            comfy_root = self.comfy_root_input.text().strip()
            self.parser = ComfyUIWorkflowParser(comfy_root if comfy_root else None)
        
        self.workflow_info = self.parser.parse_file(filepath)
        self.resolved_models.clear()
        
        # Check for errors
        if self.workflow_info.errors:
            QMessageBox.warning(
                self,
                "Parse Errors",
                "\n".join(self.workflow_info.errors)
            )
        
        # Update info display
        self._update_info_display()
        
        # Populate table
        self._populate_models_table()
        
        # Enable buttons
        has_models = len(self.workflow_info.models) > 0
        self.select_all_btn.setEnabled(has_models)
        self.select_missing_btn.setEnabled(has_models)
        self.deselect_btn.setEnabled(has_models)
        self.resolve_btn.setEnabled(has_models)
        
        self.event_bus.emit(
            Events.NOTIFICATION,
            f"Found {len(self.workflow_info.models)} model references",
            "success"
        )
    
    def _update_info_display(self) -> None:
        """Update the workflow info display."""
        if not self.workflow_info:
            return
        
        source = Path(self.workflow_info.source_file).name if self.workflow_info.source_file else "-"
        self.info_source.setText(f"Source: {source}")
        self.info_nodes.setText(f"Nodes: {self.workflow_info.node_count}")
        self.info_models.setText(f"Models: {len(self.workflow_info.models)}")
        self.info_missing.setText(f"Missing: {len(self.workflow_info.missing_models)}")
    
    def _populate_models_table(self) -> None:
        """Populate the models table with parsed models."""
        self.models_table.setRowCount(0)
        
        if not self.workflow_info:
            return
        
        missing_names = {m.name for m in self.workflow_info.missing_models}
        
        for model in self.workflow_info.models:
            row = self.models_table.rowCount()
            self.models_table.insertRow(row)
            
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(model.name in missing_names)
            self.models_table.setCellWidget(row, 0, checkbox)
            
            # Model name
            name_item = QTableWidgetItem(model.display_name)
            name_item.setToolTip(model.name)
            name_item.setData(Qt.ItemDataRole.UserRole, model)
            self.models_table.setItem(row, 1, name_item)
            
            # Type
            type_item = QTableWidgetItem(model.model_type)
            self.models_table.setItem(row, 2, type_item)
            
            # Status
            if model.name in missing_names:
                status_item = QTableWidgetItem("Missing")
                status_item.setForeground(QColor("#f38ba8"))
            else:
                status_item = QTableWidgetItem("Found")
                status_item.setForeground(QColor("#a6e3a1"))
            self.models_table.setItem(row, 3, status_item)
            
            # HF Repo (empty initially)
            self.models_table.setItem(row, 4, QTableWidgetItem("-"))
            
            # Confidence (empty initially)
            self.models_table.setItem(row, 5, QTableWidgetItem("-"))
    
    def _select_all(self) -> None:
        """Select all models."""
        for row in range(self.models_table.rowCount()):
            checkbox = self.models_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def _select_missing(self) -> None:
        """Select only missing models."""
        for row in range(self.models_table.rowCount()):
            status_item = self.models_table.item(row, 3)
            checkbox = self.models_table.cellWidget(row, 0)
            if checkbox and status_item:
                checkbox.setChecked(status_item.text() == "Missing")
    
    def _deselect_all(self) -> None:
        """Deselect all models."""
        for row in range(self.models_table.rowCount()):
            checkbox = self.models_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def _resolve_models(self) -> None:
        """Resolve selected models to HuggingFace repos."""
        if not self.workflow_info:
            return
        
        # Get selected models
        selected_models = []
        for row in range(self.models_table.rowCount()):
            checkbox = self.models_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                item = self.models_table.item(row, 1)
                if item:
                    model = item.data(Qt.ItemDataRole.UserRole)
                    if model:
                        selected_models.append(model)
        
        if not selected_models:
            QMessageBox.information(self, "No Selection", "Please select models to resolve.")
            return
        
        # Start resolver worker
        self.resolve_progress.setVisible(True)
        self.resolve_progress.setMaximum(len(selected_models))
        self.resolve_progress.setValue(0)
        self.resolve_btn.setEnabled(False)
        
        self.resolver_worker = ResolverWorker(selected_models)
        self.resolver_worker.progress.connect(self._on_resolve_progress)
        self.resolver_worker.resolved.connect(self._on_model_resolved)
        self.resolver_worker.finished.connect(self._on_resolve_finished)
        self.resolver_worker.start()
    
    @pyqtSlot(int, int)
    def _on_resolve_progress(self, current: int, total: int) -> None:
        """Handle resolve progress update."""
        self.resolve_progress.setValue(current)
        self.resolve_progress.setFormat(f"Resolving {current}/{total}...")
    
    @pyqtSlot(str, object)
    def _on_model_resolved(self, model_name: str, result: Optional[ResolvedModel]) -> None:
        """Handle model resolved."""
        self.resolved_models[model_name] = result
        
        # Update table
        for row in range(self.models_table.rowCount()):
            name_item = self.models_table.item(row, 1)
            if name_item and name_item.toolTip() == model_name:
                if result:
                    self.models_table.item(row, 4).setText(result.repo_id)
                    self.models_table.item(row, 5).setText(f"{result.confidence:.0%}")
                else:
                    self.models_table.item(row, 4).setText("Not found")
                    self.models_table.item(row, 5).setText("-")
                break
    
    @pyqtSlot()
    def _on_resolve_finished(self) -> None:
        """Handle resolve finished."""
        self.resolve_progress.setVisible(False)
        self.resolve_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        
        resolved_count = sum(1 for r in self.resolved_models.values() if r is not None)
        self.event_bus.emit(
            Events.NOTIFICATION,
            f"Resolved {resolved_count}/{len(self.resolved_models)} models",
            "success" if resolved_count > 0 else "warning"
        )
    
    def _download_selected(self) -> None:
        """Download selected resolved models."""
        comfy_root = self.comfy_root_input.text().strip()
        if not comfy_root:
            QMessageBox.warning(
                self,
                "ComfyUI Root Required",
                "Please set the ComfyUI root directory before downloading."
            )
            return
        
        # Collect downloadable models
        to_download = []
        for row in range(self.models_table.rowCount()):
            checkbox = self.models_table.cellWidget(row, 0)
            if not checkbox or not checkbox.isChecked():
                continue
            
            name_item = self.models_table.item(row, 1)
            repo_item = self.models_table.item(row, 4)
            
            if not name_item or not repo_item:
                continue
            
            model: ModelReference = name_item.data(Qt.ItemDataRole.UserRole)
            repo_id = repo_item.text()
            
            if repo_id and repo_id not in ("-", "Not found"):
                # Determine save path
                folder = ComfyUIWorkflowParser.get_model_type_folder(model.model_type)
                save_path = str(Path(comfy_root) / "models" / folder)
                
                to_download.append((repo_id, save_path, model))
        
        if not to_download:
            QMessageBox.information(
                self,
                "Nothing to Download",
                "No resolved models selected for download."
            )
            return
        
        # Add to download queue
        for repo_id, save_path, model in to_download:
            resolved = self.resolved_models.get(model.name)
            
            # Get specific file to download if resolved
            selected_files = None
            if resolved and resolved.file_path:
                selected_files = [resolved.file_path]
            
            self.download_manager.add(
                repo_id=repo_id,
                platform="huggingface",
                repo_type="model",
                save_path=save_path,
                selected_files=selected_files,
            )
        
        self.event_bus.emit(
            Events.NOTIFICATION,
            f"Added {len(to_download)} downloads to queue",
            "success"
        )
        
        # Emit signal to switch to downloads tab
        if to_download:
            self.download_requested.emit(to_download[0][0], "huggingface", to_download[0][1])
