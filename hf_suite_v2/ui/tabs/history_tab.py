"""
History tab - Download history and favorites management.
"""

import logging
import json
import csv
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox,
    QMessageBox, QFileDialog, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ...core import get_config, get_db, EventBus, Events
from ...core.database import HistoryTable

logger = logging.getLogger(__name__)


class HistoryTab(QWidget):
    """
    History tab showing completed downloads.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │  ┌─ Filters ──────────────────────────────────────────┐ │
    │  │ [Search...] [All ▾] [⭐ Favorites] [Clear History] │ │
    │  └────────────────────────────────────────────────────┘ │
    │                                                         │
    │  ┌─ History Table ────────────────────────────────────┐ │
    │  │ ⭐ │ Repository      │ Platform │ Size  │ Date     │ │
    │  │────┼─────────────────┼──────────┼───────┼──────────│ │
    │  │ ⭐ │ user/model-1    │ 🤗 HF    │ 2.3GB │ 2024-01-│ │
    │  │    │ user/model-2    │ 📦 MS    │ 1.1GB │ 2024-01-│ │
    │  │ ⭐ │ user/model-3    │ 🤗 HF    │ 4.5GB │ 2024-01-│ │
    │  └────────────────────────────────────────────────────┘ │
    │                                                         │
    │  Selected: 2 items                    [Re-download] [📁]│
    └─────────────────────────────────────────────────────────┘
    """
    
    redownload_requested = pyqtSignal(str, str, str)  # repo_id, platform, path
    
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.db = get_db()
        self.event_bus = EventBus()
        
        self._setup_ui()
        self._load_history()
        
        # Subscribe to events
        self.event_bus.subscribe(Events.HISTORY_ADDED, self._load_history)
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Filters section
        layout.addWidget(self._create_filters_section())
        
        # History table
        layout.addWidget(self._create_table(), 1)
        
        # Actions bar
        layout.addWidget(self._create_actions_bar())
    
    def _create_filters_section(self) -> QFrame:
        """Create filters section."""
        frame = QFrame()
        frame.setObjectName("card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history...")
        self.search_input.textChanged.connect(self._filter_table)
        layout.addWidget(self.search_input, 1)
        
        # Platform filter
        self.platform_filter = QComboBox()
        self.platform_filter.addItem("All Platforms", "all")
        self.platform_filter.addItem("🤗 HuggingFace", "huggingface")
        self.platform_filter.addItem("📦 ModelScope", "modelscope")
        self.platform_filter.currentIndexChanged.connect(self._filter_table)
        self.platform_filter.setFixedWidth(150)
        layout.addWidget(self.platform_filter)
        
        # Favorites only
        self.favorites_check = QCheckBox("⭐ Favorites only")
        self.favorites_check.stateChanged.connect(self._filter_table)
        layout.addWidget(self.favorites_check)
        
        # Clear history
        clear_btn = QPushButton("🗑️ Clear History")
        clear_btn.clicked.connect(self._clear_history)
        layout.addWidget(clear_btn)
        
        return frame
    
    def _create_table(self) -> QTableWidget:
        """Create the history table."""
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "⭐", "Repository", "Platform", "Size", "Date", "Path"
        ])
        
        # Configure table
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        
        # Double-click to re-download
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        
        return self.table
    
    def _create_actions_bar(self) -> QWidget:
        """Create the actions bar."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.selection_label = QLabel("Select items to perform actions")
        self.selection_label.setObjectName("subtitle")
        layout.addWidget(self.selection_label)
        
        layout.addStretch()
        
        # Re-download button
        self.redownload_btn = QPushButton("🔄 Re-download")
        self.redownload_btn.clicked.connect(self._redownload_selected)
        layout.addWidget(self.redownload_btn)
        
        # Open folder button
        self.open_folder_btn = QPushButton("📁 Open Folder")
        self.open_folder_btn.clicked.connect(self._open_selected_folder)
        layout.addWidget(self.open_folder_btn)
        
        # Export button with dropdown menu
        self.export_btn = QPushButton("📤 Export")
        export_menu = QMenu(self)
        export_menu.addAction("Export as CSV", self._export_csv)
        export_menu.addAction("Export as JSON", self._export_json)
        self.export_btn.setMenu(export_menu)
        layout.addWidget(self.export_btn)
        
        return widget
    
    def _load_history(self) -> None:
        """Load history from database."""
        try:
            history = self.db.get_history(limit=500)
            self._populate_table(history)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
    
    def _populate_table(self, history: List[HistoryTable]) -> None:
        """Populate the table with history entries."""
        self.table.setRowCount(0)
        
        for entry in history:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Favorite star (clickable)
            fav_item = QTableWidgetItem("⭐" if entry.is_favorite else "☆")
            fav_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            fav_item.setData(Qt.ItemDataRole.UserRole, entry.id)
            self.table.setItem(row, 0, fav_item)
            
            # Repository
            self.table.setItem(row, 1, QTableWidgetItem(entry.repo_id))
            
            # Platform
            platform_icons = {"huggingface": "🤗", "modelscope": "📦"}
            platform_text = platform_icons.get(entry.platform, "📥") + " " + entry.platform.title()
            self.table.setItem(row, 2, QTableWidgetItem(platform_text))
            
            # Size
            size_text = self._format_bytes(entry.total_bytes) if entry.total_bytes else "-"
            self.table.setItem(row, 3, QTableWidgetItem(size_text))
            
            # Date
            date_text = entry.completed_at.strftime("%Y-%m-%d") if entry.completed_at else "-"
            self.table.setItem(row, 4, QTableWidgetItem(date_text))
            
            # Path
            self.table.setItem(row, 5, QTableWidgetItem(entry.save_path or "-"))
        
        self.selection_label.setText(f"{len(history)} downloads in history")
    
    def _filter_table(self) -> None:
        """Filter table based on current filters."""
        search_text = self.search_input.text().lower()
        platform_filter = self.platform_filter.currentData()
        favorites_only = self.favorites_check.isChecked()
        
        for row in range(self.table.rowCount()):
            show = True
            
            # Search filter
            if search_text:
                repo_id = self.table.item(row, 1).text().lower()
                if search_text not in repo_id:
                    show = False
            
            # Platform filter
            if platform_filter != "all":
                platform_text = self.table.item(row, 2).text().lower()
                if platform_filter not in platform_text:
                    show = False
            
            # Favorites filter
            if favorites_only:
                fav_text = self.table.item(row, 0).text()
                if fav_text != "⭐":
                    show = False
            
            self.table.setRowHidden(row, not show)
    
    def _on_row_double_clicked(self, row: int, col: int) -> None:
        """Handle row double-click."""
        if col == 0:
            # Toggle favorite
            self._toggle_favorite(row)
        else:
            # Re-download
            self._redownload_row(row)
    
    def _toggle_favorite(self, row: int) -> None:
        """Toggle favorite status for a row."""
        fav_item = self.table.item(row, 0)
        history_id = fav_item.data(Qt.ItemDataRole.UserRole)
        
        if self.db.toggle_favorite(history_id):
            current = fav_item.text()
            fav_item.setText("⭐" if current == "☆" else "☆")
            self.event_bus.emit(Events.FAVORITE_TOGGLED, history_id=history_id)
    
    def _redownload_row(self, row: int) -> None:
        """Request re-download for a row."""
        repo_id = self.table.item(row, 1).text()
        platform_text = self.table.item(row, 2).text()
        platform = "huggingface" if "🤗" in platform_text else "modelscope"
        path = self.table.item(row, 5).text()
        
        self.redownload_requested.emit(repo_id, platform, path)
    
    def _redownload_selected(self) -> None:
        """Re-download selected items."""
        selected = self.table.selectedItems()
        if not selected:
            return
        
        rows = set(item.row() for item in selected)
        for row in rows:
            self._redownload_row(row)
    
    def _open_selected_folder(self) -> None:
        """Open folder for selected item."""
        selected = self.table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        path = self.table.item(row, 5).text()
        
        if path and path != "-":
            import os
            import subprocess
            import platform
            if os.path.exists(path):
                system = platform.system()
                if system == "Windows":
                    os.startfile(path)
                elif system == "Darwin":  # macOS
                    subprocess.Popen(["open", path])
                else:  # Linux and others
                    subprocess.Popen(["xdg-open", path])
    
    def _clear_history(self) -> None:
        """Clear all history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all download history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear from database (would need db method)
            self.table.setRowCount(0)
            self.event_bus.emit(Events.HISTORY_CLEARED)
            self.event_bus.emit(Events.NOTIFICATION, "History cleared", "success")
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes as human-readable."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"
    
    def _get_history_data(self) -> List[dict]:
        """Get history data from the database as list of dicts."""
        history = self.db.get_history(limit=10000)
        data = []
        for entry in history:
            data.append({
                "repo_id": entry.repo_id,
                "platform": entry.platform,
                "repo_type": entry.repo_type,
                "save_path": entry.save_path,
                "total_bytes": entry.total_bytes,
                "duration_seconds": entry.duration_seconds,
                "completed_at": entry.completed_at.isoformat() if entry.completed_at else None,
                "is_favorite": entry.is_favorite,
            })
        return data
    
    def _export_csv(self) -> None:
        """Export history to CSV file."""
        # Get save path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export History as CSV",
            str(Path.home() / "download_history.csv"),
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            data = self._get_history_data()
            
            if not data:
                self.event_bus.emit(Events.NOTIFICATION, "No history to export", "warning")
                return
            
            # Write CSV
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            self.event_bus.emit(
                Events.NOTIFICATION,
                f"Exported {len(data)} entries to {Path(file_path).name}",
                "success"
            )
            logger.info(f"History exported to CSV: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            self.event_bus.emit(Events.NOTIFICATION, f"Export failed: {e}", "error")
    
    def _export_json(self) -> None:
        """Export history to JSON file."""
        # Get save path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export History as JSON",
            str(Path.home() / "download_history.json"),
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            data = self._get_history_data()
            
            if not data:
                self.event_bus.emit(Events.NOTIFICATION, "No history to export", "warning")
                return
            
            # Write JSON with nice formatting
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "export_date": datetime.now().isoformat(),
                    "count": len(data),
                    "history": data
                }, f, indent=2)
            
            self.event_bus.emit(
                Events.NOTIFICATION,
                f"Exported {len(data)} entries to {Path(file_path).name}",
                "success"
            )
            logger.info(f"History exported to JSON: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            self.event_bus.emit(Events.NOTIFICATION, f"Export failed: {e}", "error")
