"""
Reusable path selector widget with browse button.

Provides a standardized way to select directories or files
across the application with consistent styling and behavior.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal

logger = logging.getLogger(__name__)


class PathSelector(QWidget):
    """
    A reusable widget for selecting file paths with a browse button.
    
    Features:
    - Text input for manual path entry
    - Browse button to open file dialog
    - Supports both file and directory selection
    - Emits signal when path changes
    - Validates path existence (optional)
    
    Usage:
        selector = PathSelector(
            placeholder="Select save directory...",
            mode="directory",
            validate=True
        )
        selector.path_changed.connect(self.on_path_changed)
    """
    
    # Signal emitted when path changes
    path_changed = pyqtSignal(str)
    
    def __init__(
        self,
        placeholder: str = "Select path...",
        mode: str = "directory",  # "directory" or "file"
        initial_path: str = "",
        validate: bool = False,
        browse_icon: str = "📁",
        file_filter: str = "",
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the path selector.
        
        Args:
            placeholder: Placeholder text for the input
            mode: "directory" for folders, "file" for files
            initial_path: Initial path to display
            validate: If True, highlight invalid paths
            browse_icon: Icon for the browse button
            file_filter: File filter for file mode (e.g., "JSON Files (*.json)")
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.mode = mode
        self.validate = validate
        self.file_filter = file_filter
        
        self._setup_ui(placeholder, browse_icon)
        
        if initial_path:
            self.set_path(initial_path)
    
    def _setup_ui(self, placeholder: str, browse_icon: str) -> None:
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Path input
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(placeholder)
        self.path_input.textChanged.connect(self._on_text_changed)
        self.path_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.path_input)
        
        # Browse button
        self.browse_btn = QPushButton(browse_icon)
        self.browse_btn.setFixedWidth(40)
        self.browse_btn.setToolTip("Browse...")
        self.browse_btn.clicked.connect(self._browse)
        layout.addWidget(self.browse_btn)
    
    def _browse(self) -> None:
        """Open file/directory dialog."""
        start_path = self.path_input.text() or os.path.expanduser("~")
        
        if self.mode == "directory":
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Directory",
                start_path
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select File",
                start_path,
                self.file_filter
            )
        
        if path:
            self.set_path(path)
    
    def _on_text_changed(self, text: str) -> None:
        """Handle text input changes."""
        if self.validate:
            self._update_validation_style(text)
        
        self.path_changed.emit(text)
    
    def _update_validation_style(self, path: str) -> None:
        """Update input style based on path validity."""
        if not path:
            self.path_input.setStyleSheet("")
            return
        
        path_obj = Path(path)
        
        if self.mode == "directory":
            is_valid = path_obj.is_dir()
        else:
            is_valid = path_obj.is_file()
        
        if is_valid:
            self.path_input.setStyleSheet("border: 1px solid #a6e3a1;")
        else:
            self.path_input.setStyleSheet("border: 1px solid #f38ba8;")
    
    def set_path(self, path: str) -> None:
        """Set the current path."""
        self.path_input.setText(path)
    
    def get_path(self) -> str:
        """Get the current path."""
        return self.path_input.text().strip()
    
    def path(self) -> str:
        """Alias for get_path() for convenience."""
        return self.get_path()
    
    def is_valid(self) -> bool:
        """Check if the current path is valid."""
        path = self.get_path()
        if not path:
            return False
        
        path_obj = Path(path)
        
        if self.mode == "directory":
            return path_obj.is_dir()
        else:
            return path_obj.is_file()
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the widget."""
        self.path_input.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)
    
    def set_placeholder(self, text: str) -> None:
        """Set placeholder text."""
        self.path_input.setPlaceholderText(text)
    
    def set_fixed_width(self, width: int) -> None:
        """Set fixed width for the path input."""
        self.path_input.setFixedWidth(width)
    
    def clear(self) -> None:
        """Clear the path input."""
        self.path_input.clear()


class SavePathSelector(PathSelector):
    """
    Specialized path selector for save directories.
    
    Pre-configured for directory selection with appropriate defaults.
    """
    
    def __init__(
        self,
        initial_path: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(
            placeholder="Save directory...",
            mode="directory",
            initial_path=initial_path,
            validate=True,
            browse_icon="📁",
            parent=parent
        )


class FileSelector(PathSelector):
    """
    Specialized path selector for file selection.
    
    Pre-configured for file selection with filter support.
    """
    
    def __init__(
        self,
        placeholder: str = "Select file...",
        file_filter: str = "All Files (*.*)",
        initial_path: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(
            placeholder=placeholder,
            mode="file",
            initial_path=initial_path,
            validate=True,
            browse_icon="📄",
            file_filter=file_filter,
            parent=parent
        )
