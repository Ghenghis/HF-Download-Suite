"""
Profiles tab - Manage download profiles and path presets.
"""

import logging
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QAbstractItemView, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...core import get_config, get_database, EventBus, Events
from ...core.constants import PLATFORM_KEYS, MODEL_TYPES

logger = logging.getLogger(__name__)


class ProfileDialog(QDialog):
    """Dialog for creating/editing a download profile."""
    
    def __init__(self, parent=None, profile: dict = None):
        super().__init__(parent)
        self.profile = profile or {}
        self.setWindowTitle("Edit Profile" if profile else "New Profile")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._load_profile()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., SDXL Models, LoRA Collection")
        form.addRow("Profile Name:", self.name_input)
        
        # Platform
        self.platform_combo = QComboBox()
        for platform in PLATFORM_KEYS:
            self.platform_combo.addItem(platform.title(), platform)
        form.addRow("Platform:", self.platform_combo)
        
        # Default path
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Default save directory")
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)
        form.addRow("Default Path:", path_layout)
        
        # Model type filter
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types", "")
        for model_type in MODEL_TYPES:
            self.type_combo.addItem(model_type.title(), model_type)
        form.addRow("Model Type:", self.type_combo)
        
        # File filters
        self.filters_input = QLineEdit()
        self.filters_input.setPlaceholderText("e.g., *.safetensors, *.gguf (comma separated)")
        form.addRow("File Filters:", self.filters_input)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Default Directory",
            self.path_input.text() or str(Path.home())
        )
        if path:
            self.path_input.setText(path)
    
    def _load_profile(self):
        if self.profile:
            self.name_input.setText(self.profile.get("name", ""))
            
            platform = self.profile.get("platform", "")
            idx = self.platform_combo.findData(platform)
            if idx >= 0:
                self.platform_combo.setCurrentIndex(idx)
            
            self.path_input.setText(self.profile.get("default_path", ""))
            
            model_type = self.profile.get("model_type", "")
            idx = self.type_combo.findData(model_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            
            filters = self.profile.get("file_filters", [])
            self.filters_input.setText(", ".join(filters) if filters else "")
    
    def get_profile(self) -> dict:
        filters_text = self.filters_input.text().strip()
        filters = [f.strip() for f in filters_text.split(",") if f.strip()] if filters_text else []
        
        return {
            "name": self.name_input.text().strip(),
            "platform": self.platform_combo.currentData(),
            "default_path": self.path_input.text().strip(),
            "model_type": self.type_combo.currentData(),
            "file_filters": filters,
        }


class LocationDialog(QDialog):
    """Dialog for creating/editing a path location."""
    
    def __init__(self, parent=None, location: dict = None):
        super().__init__(parent)
        self.location = location or {}
        self.setWindowTitle("Edit Location" if location else "New Location")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._load_location()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., ComfyUI Checkpoints, LM Studio Models")
        form.addRow("Location Name:", self.name_input)
        
        # Path
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Directory path")
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)
        form.addRow("Path:", path_layout)
        
        # Tool type
        self.tool_combo = QComboBox()
        self.tool_combo.addItem("Custom", "custom")
        self.tool_combo.addItem("ComfyUI", "comfyui")
        self.tool_combo.addItem("Automatic1111", "a1111")
        self.tool_combo.addItem("Forge", "forge")
        self.tool_combo.addItem("LM Studio", "lmstudio")
        self.tool_combo.addItem("Ollama", "ollama")
        form.addRow("Tool:", self.tool_combo)
        
        # Model type
        self.type_combo = QComboBox()
        self.type_combo.addItem("General", "")
        for model_type in MODEL_TYPES:
            self.type_combo.addItem(model_type.title(), model_type)
        form.addRow("Model Type:", self.type_combo)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Directory",
            self.path_input.text() or str(Path.home())
        )
        if path:
            self.path_input.setText(path)
    
    def _load_location(self):
        if self.location:
            self.name_input.setText(self.location.get("name", ""))
            self.path_input.setText(self.location.get("path", ""))
            
            tool = self.location.get("tool_type", "custom")
            idx = self.tool_combo.findData(tool)
            if idx >= 0:
                self.tool_combo.setCurrentIndex(idx)
            
            model_type = self.location.get("model_type", "")
            idx = self.type_combo.findData(model_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
    
    def get_location(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "path": self.path_input.text().strip(),
            "tool_type": self.tool_combo.currentData(),
            "model_type": self.type_combo.currentData(),
        }


class ProfilesTab(QWidget):
    """
    Profiles tab for managing download profiles and path presets.
    
    Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │  ┌─ Download Profiles ────────────────────────────────────────┐ │
    │  │ Name          | Platform    | Default Path    | Type       │ │
    │  │ SDXL Models   | HuggingFace | D:/AI/models    | checkpoint │ │
    │  │ LoRA Collect..| HuggingFace | D:/AI/loras     | lora       │ │
    │  │                                                            │ │
    │  │ [New Profile] [Edit] [Delete]           [Set as Default]   │ │
    │  └────────────────────────────────────────────────────────────┘ │
    │  ┌─ Path Locations ───────────────────────────────────────────┐ │
    │  │ Name              | Path               | Tool     | Type   │ │
    │  │ ComfyUI Checkpts  | C:/ComfyUI/models  | ComfyUI  | ckpt   │ │
    │  │ LM Studio         | ~/.lmstudio/models | LMStudio | gguf   │ │
    │  │                                                            │ │
    │  │ [New Location] [Edit] [Delete]              [Auto-Detect]  │ │
    │  └────────────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    profile_selected = pyqtSignal(dict)  # Emits selected profile data
    
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.db = get_database()
        self.event_bus = EventBus()
        
        self._setup_ui()
        self._setup_connections()
        self._load_data()
        
        logger.info("Profiles tab initialized")
    
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Splitter for profiles and locations
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Profiles section
        splitter.addWidget(self._create_profiles_section())
        
        # Locations section
        splitter.addWidget(self._create_locations_section())
        
        splitter.setSizes([300, 300])
        layout.addWidget(splitter)
    
    def _create_profiles_section(self) -> QGroupBox:
        """Create the download profiles section."""
        group = QGroupBox("Download Profiles")
        layout = QVBoxLayout(group)
        
        # Profiles table
        self.profiles_table = QTableWidget()
        self.profiles_table.setColumnCount(5)
        self.profiles_table.setHorizontalHeaderLabels([
            "Name", "Platform", "Default Path", "Model Type", "Filters"
        ])
        
        header = self.profiles_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        
        self.profiles_table.setColumnWidth(1, 100)
        self.profiles_table.setColumnWidth(3, 100)
        
        self.profiles_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.profiles_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.profiles_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.profiles_table)
        
        # Actions bar
        actions = QHBoxLayout()
        
        self.new_profile_btn = QPushButton("New Profile")
        actions.addWidget(self.new_profile_btn)
        
        self.edit_profile_btn = QPushButton("Edit")
        self.edit_profile_btn.setEnabled(False)
        actions.addWidget(self.edit_profile_btn)
        
        self.delete_profile_btn = QPushButton("Delete")
        self.delete_profile_btn.setEnabled(False)
        actions.addWidget(self.delete_profile_btn)
        
        actions.addStretch()
        
        self.default_profile_btn = QPushButton("Set as Default")
        self.default_profile_btn.setEnabled(False)
        actions.addWidget(self.default_profile_btn)
        
        layout.addLayout(actions)
        
        return group
    
    def _create_locations_section(self) -> QGroupBox:
        """Create the path locations section."""
        group = QGroupBox("Path Locations")
        layout = QVBoxLayout(group)
        
        # Locations table
        self.locations_table = QTableWidget()
        self.locations_table.setColumnCount(4)
        self.locations_table.setHorizontalHeaderLabels([
            "Name", "Path", "Tool", "Model Type"
        ])
        
        header = self.locations_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.locations_table.setColumnWidth(2, 100)
        self.locations_table.setColumnWidth(3, 100)
        
        self.locations_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.locations_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.locations_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.locations_table)
        
        # Actions bar
        actions = QHBoxLayout()
        
        self.new_location_btn = QPushButton("New Location")
        actions.addWidget(self.new_location_btn)
        
        self.edit_location_btn = QPushButton("Edit")
        self.edit_location_btn.setEnabled(False)
        actions.addWidget(self.edit_location_btn)
        
        self.delete_location_btn = QPushButton("Delete")
        self.delete_location_btn.setEnabled(False)
        actions.addWidget(self.delete_location_btn)
        
        actions.addStretch()
        
        self.detect_btn = QPushButton("Auto-Detect Tools")
        actions.addWidget(self.detect_btn)
        
        layout.addLayout(actions)
        
        return group
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Profile buttons
        self.new_profile_btn.clicked.connect(self._new_profile)
        self.edit_profile_btn.clicked.connect(self._edit_profile)
        self.delete_profile_btn.clicked.connect(self._delete_profile)
        self.default_profile_btn.clicked.connect(self._set_default_profile)
        
        # Location buttons
        self.new_location_btn.clicked.connect(self._new_location)
        self.edit_location_btn.clicked.connect(self._edit_location)
        self.delete_location_btn.clicked.connect(self._delete_location)
        self.detect_btn.clicked.connect(self._auto_detect_tools)
        
        # Table selection
        self.profiles_table.itemSelectionChanged.connect(self._on_profile_selection_changed)
        self.locations_table.itemSelectionChanged.connect(self._on_location_selection_changed)
        
        # Double-click to edit
        self.profiles_table.doubleClicked.connect(self._edit_profile)
        self.locations_table.doubleClicked.connect(self._edit_location)
    
    def _load_data(self) -> None:
        """Load profiles and locations from database."""
        self._load_profiles()
        self._load_locations()
    
    def _load_profiles(self) -> None:
        """Load profiles from database."""
        self.profiles_table.setRowCount(0)
        
        # Get profiles from settings (stored as JSON)
        profiles_json = self.db.get_setting("profiles", "[]")
        try:
            import json
            profiles = json.loads(profiles_json)
        except:
            profiles = []
        
        for profile in profiles:
            row = self.profiles_table.rowCount()
            self.profiles_table.insertRow(row)
            
            name_item = QTableWidgetItem(profile.get("name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, profile)
            self.profiles_table.setItem(row, 0, name_item)
            
            self.profiles_table.setItem(row, 1, QTableWidgetItem(
                profile.get("platform", "").title()
            ))
            self.profiles_table.setItem(row, 2, QTableWidgetItem(
                profile.get("default_path", "")
            ))
            self.profiles_table.setItem(row, 3, QTableWidgetItem(
                profile.get("model_type", "").title() or "All"
            ))
            
            filters = profile.get("file_filters", [])
            self.profiles_table.setItem(row, 4, QTableWidgetItem(
                ", ".join(filters) if filters else "-"
            ))
    
    def _load_locations(self) -> None:
        """Load locations from database."""
        self.locations_table.setRowCount(0)
        
        locations = self.db.get_locations()
        
        for loc in locations:
            row = self.locations_table.rowCount()
            self.locations_table.insertRow(row)
            
            name_item = QTableWidgetItem(loc.get("name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, loc)
            self.locations_table.setItem(row, 0, name_item)
            
            self.locations_table.setItem(row, 1, QTableWidgetItem(loc.get("path", "")))
            self.locations_table.setItem(row, 2, QTableWidgetItem(
                loc.get("tool_type", "custom").title()
            ))
            self.locations_table.setItem(row, 3, QTableWidgetItem(
                loc.get("model_type", "").title() or "General"
            ))
    
    def _save_profiles(self) -> None:
        """Save profiles to database."""
        import json
        
        profiles = []
        for row in range(self.profiles_table.rowCount()):
            item = self.profiles_table.item(row, 0)
            if item:
                profile = item.data(Qt.ItemDataRole.UserRole)
                if profile:
                    profiles.append(profile)
        
        self.db.set_setting("profiles", json.dumps(profiles))
    
    def _on_profile_selection_changed(self) -> None:
        """Handle profile selection change."""
        has_selection = len(self.profiles_table.selectedItems()) > 0
        self.edit_profile_btn.setEnabled(has_selection)
        self.delete_profile_btn.setEnabled(has_selection)
        self.default_profile_btn.setEnabled(has_selection)
    
    def _on_location_selection_changed(self) -> None:
        """Handle location selection change."""
        has_selection = len(self.locations_table.selectedItems()) > 0
        self.edit_location_btn.setEnabled(has_selection)
        self.delete_location_btn.setEnabled(has_selection)
    
    def _new_profile(self) -> None:
        """Create a new profile."""
        dialog = ProfileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            profile = dialog.get_profile()
            if not profile["name"]:
                QMessageBox.warning(self, "Invalid Profile", "Profile name is required.")
                return
            
            row = self.profiles_table.rowCount()
            self.profiles_table.insertRow(row)
            
            name_item = QTableWidgetItem(profile["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, profile)
            self.profiles_table.setItem(row, 0, name_item)
            
            self.profiles_table.setItem(row, 1, QTableWidgetItem(profile["platform"].title()))
            self.profiles_table.setItem(row, 2, QTableWidgetItem(profile["default_path"]))
            self.profiles_table.setItem(row, 3, QTableWidgetItem(
                profile["model_type"].title() or "All"
            ))
            self.profiles_table.setItem(row, 4, QTableWidgetItem(
                ", ".join(profile["file_filters"]) if profile["file_filters"] else "-"
            ))
            
            self._save_profiles()
            self.event_bus.emit(Events.NOTIFICATION, f"Profile '{profile['name']}' created", "success")
    
    def _edit_profile(self) -> None:
        """Edit selected profile."""
        row = self.profiles_table.currentRow()
        if row < 0:
            return
        
        item = self.profiles_table.item(row, 0)
        if not item:
            return
        
        profile = item.data(Qt.ItemDataRole.UserRole)
        
        dialog = ProfileDialog(self, profile)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_profile()
            if not updated["name"]:
                QMessageBox.warning(self, "Invalid Profile", "Profile name is required.")
                return
            
            item.setText(updated["name"])
            item.setData(Qt.ItemDataRole.UserRole, updated)
            
            self.profiles_table.item(row, 1).setText(updated["platform"].title())
            self.profiles_table.item(row, 2).setText(updated["default_path"])
            self.profiles_table.item(row, 3).setText(updated["model_type"].title() or "All")
            self.profiles_table.item(row, 4).setText(
                ", ".join(updated["file_filters"]) if updated["file_filters"] else "-"
            )
            
            self._save_profiles()
            self.event_bus.emit(Events.NOTIFICATION, f"Profile '{updated['name']}' updated", "success")
    
    def _delete_profile(self) -> None:
        """Delete selected profile."""
        row = self.profiles_table.currentRow()
        if row < 0:
            return
        
        item = self.profiles_table.item(row, 0)
        if not item:
            return
        
        name = item.text()
        
        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Are you sure you want to delete profile '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.profiles_table.removeRow(row)
            self._save_profiles()
            self.event_bus.emit(Events.NOTIFICATION, f"Profile '{name}' deleted", "info")
    
    def _set_default_profile(self) -> None:
        """Set selected profile as default."""
        row = self.profiles_table.currentRow()
        if row < 0:
            return
        
        item = self.profiles_table.item(row, 0)
        if not item:
            return
        
        profile = item.data(Qt.ItemDataRole.UserRole)
        self.db.set_setting("default_profile", profile["name"])
        self.event_bus.emit(
            Events.NOTIFICATION,
            f"'{profile['name']}' set as default profile",
            "success"
        )
    
    def _new_location(self) -> None:
        """Create a new location."""
        dialog = LocationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            location = dialog.get_location()
            if not location["name"] or not location["path"]:
                QMessageBox.warning(self, "Invalid Location", "Name and path are required.")
                return
            
            # Add to database
            self.db.add_location(
                name=location["name"],
                path=location["path"],
                tool_type=location["tool_type"],
                model_type=location["model_type"],
            )
            
            self._load_locations()
            self.event_bus.emit(Events.NOTIFICATION, f"Location '{location['name']}' added", "success")
    
    def _edit_location(self) -> None:
        """Edit selected location."""
        row = self.locations_table.currentRow()
        if row < 0:
            return
        
        item = self.locations_table.item(row, 0)
        if not item:
            return
        
        location = item.data(Qt.ItemDataRole.UserRole)
        
        dialog = LocationDialog(self, location)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_location()
            if not updated["name"] or not updated["path"]:
                QMessageBox.warning(self, "Invalid Location", "Name and path are required.")
                return
            
            # Update in database
            loc_id = location.get("id")
            if loc_id:
                self.db.delete_location(loc_id)
            
            self.db.add_location(
                name=updated["name"],
                path=updated["path"],
                tool_type=updated["tool_type"],
                model_type=updated["model_type"],
            )
            
            self._load_locations()
            self.event_bus.emit(Events.NOTIFICATION, f"Location '{updated['name']}' updated", "success")
    
    def _delete_location(self) -> None:
        """Delete selected location."""
        row = self.locations_table.currentRow()
        if row < 0:
            return
        
        item = self.locations_table.item(row, 0)
        if not item:
            return
        
        location = item.data(Qt.ItemDataRole.UserRole)
        name = location.get("name", "")
        
        reply = QMessageBox.question(
            self,
            "Delete Location",
            f"Are you sure you want to delete location '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            loc_id = location.get("id")
            if loc_id:
                self.db.delete_location(loc_id)
            self._load_locations()
            self.event_bus.emit(Events.NOTIFICATION, f"Location '{name}' deleted", "info")
    
    def _auto_detect_tools(self) -> None:
        """Auto-detect AI tool installations."""
        detected = []
        
        # Common paths to check
        home = Path.home()
        
        tool_paths = [
            # ComfyUI
            ("ComfyUI Checkpoints", home / "ComfyUI" / "models" / "checkpoints", "comfyui", "checkpoint"),
            ("ComfyUI LoRAs", home / "ComfyUI" / "models" / "loras", "comfyui", "lora"),
            ("ComfyUI VAE", home / "ComfyUI" / "models" / "vae", "comfyui", "vae"),
            
            # LM Studio
            ("LM Studio Models", home / ".lmstudio" / "models", "lmstudio", "gguf"),
            
            # Ollama
            ("Ollama Models", home / ".ollama" / "models", "ollama", "gguf"),
            
            # HuggingFace cache
            ("HuggingFace Cache", home / ".cache" / "huggingface" / "hub", "custom", ""),
            
            # A1111 common paths
            ("A1111 Models", home / "stable-diffusion-webui" / "models" / "Stable-diffusion", "a1111", "checkpoint"),
        ]
        
        # Windows-specific paths
        import platform
        if platform.system() == "Windows":
            for drive in ["C:", "D:", "E:"]:
                tool_paths.extend([
                    (f"ComfyUI ({drive})", Path(f"{drive}/ComfyUI/models/checkpoints"), "comfyui", "checkpoint"),
                    (f"A1111 ({drive})", Path(f"{drive}/stable-diffusion-webui/models/Stable-diffusion"), "a1111", "checkpoint"),
                ])
        
        existing_paths = {
            self.locations_table.item(row, 1).text()
            for row in range(self.locations_table.rowCount())
            if self.locations_table.item(row, 1)
        }
        
        for name, path, tool, model_type in tool_paths:
            if path.exists() and str(path) not in existing_paths:
                self.db.add_location(
                    name=name,
                    path=str(path),
                    tool_type=tool,
                    model_type=model_type,
                )
                detected.append(name)
        
        self._load_locations()
        
        if detected:
            self.event_bus.emit(
                Events.NOTIFICATION,
                f"Detected {len(detected)} new locations",
                "success"
            )
        else:
            self.event_bus.emit(
                Events.NOTIFICATION,
                "No new tool installations detected",
                "info"
            )
