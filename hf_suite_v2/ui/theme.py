"""
Theme management and QSS styling.

Enhanced with better visual hierarchy, contrast, and spacing.
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

# Theme color definitions - 15+ themes with variety
THEMES = {
    # ============================================
    # DARK THEMES
    # ============================================
    "dark": {
        "name": "Dark (Default)",
        "bg_primary": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_tertiary": "#0f3460",
        "bg_input": "#1a1a2e",
        "bg_hover": "#1f4068",
        "bg_selected": "#e94560",
        "text_primary": "#eaeaea",
        "text_secondary": "#b8b8b8",
        "text_muted": "#666680",
        "accent": "#e94560",
        "accent_hover": "#ff6b6b",
        "accent_dark": "#c73e54",
        "success": "#00d26a",
        "success_bg": "#00d26a20",
        "warning": "#ffc107",
        "warning_bg": "#ffc10720",
        "error": "#ff4757",
        "error_bg": "#ff475720",
        "border": "#0f3460",
        "border_light": "#16213e",
        "border_focus": "#e94560",
        "header_bg": "#0f0f1a",
        "statusbar_bg": "#0f0f1a",
        "separator": "#0f3460",
    },
    
    "midnight_blue": {
        "name": "Midnight Blue",
        "bg_primary": "#0a1628",
        "bg_secondary": "#132238",
        "bg_tertiary": "#1c3148",
        "bg_input": "#0a1628",
        "bg_hover": "#254058",
        "bg_selected": "#3498db40",
        "text_primary": "#ecf0f1",
        "text_secondary": "#bdc3c7",
        "text_muted": "#7f8c8d",
        "accent": "#3498db",
        "accent_hover": "#5dade2",
        "accent_dark": "#2980b9",
        "success": "#2ecc71",
        "success_bg": "#2ecc7120",
        "warning": "#f39c12",
        "warning_bg": "#f39c1220",
        "error": "#e74c3c",
        "error_bg": "#e74c3c20",
        "border": "#1c3148",
        "border_light": "#132238",
        "border_focus": "#3498db",
        "header_bg": "#061220",
        "statusbar_bg": "#061220",
        "separator": "#1c3148",
    },
    
    "dracula": {
        "name": "Dracula",
        "bg_primary": "#282a36",
        "bg_secondary": "#343746",
        "bg_tertiary": "#44475a",
        "bg_input": "#282a36",
        "bg_hover": "#4d5066",
        "bg_selected": "#bd93f940",
        "text_primary": "#f8f8f2",
        "text_secondary": "#c0c0c0",
        "text_muted": "#6272a4",
        "accent": "#bd93f9",
        "accent_hover": "#d4b8ff",
        "accent_dark": "#9d79d9",
        "success": "#50fa7b",
        "success_bg": "#50fa7b20",
        "warning": "#ffb86c",
        "warning_bg": "#ffb86c20",
        "error": "#ff5555",
        "error_bg": "#ff555520",
        "border": "#44475a",
        "border_light": "#343746",
        "border_focus": "#bd93f9",
        "header_bg": "#21222c",
        "statusbar_bg": "#21222c",
        "separator": "#44475a",
    },
    
    "nord": {
        "name": "Nord",
        "bg_primary": "#2e3440",
        "bg_secondary": "#3b4252",
        "bg_tertiary": "#434c5e",
        "bg_input": "#2e3440",
        "bg_hover": "#4c566a",
        "bg_selected": "#88c0d040",
        "text_primary": "#eceff4",
        "text_secondary": "#d8dee9",
        "text_muted": "#4c566a",
        "accent": "#88c0d0",
        "accent_hover": "#8fbcbb",
        "accent_dark": "#5e81ac",
        "success": "#a3be8c",
        "success_bg": "#a3be8c20",
        "warning": "#ebcb8b",
        "warning_bg": "#ebcb8b20",
        "error": "#bf616a",
        "error_bg": "#bf616a20",
        "border": "#434c5e",
        "border_light": "#3b4252",
        "border_focus": "#88c0d0",
        "header_bg": "#242933",
        "statusbar_bg": "#242933",
        "separator": "#434c5e",
    },
    
    "monokai": {
        "name": "Monokai",
        "bg_primary": "#272822",
        "bg_secondary": "#3e3d32",
        "bg_tertiary": "#49483e",
        "bg_input": "#272822",
        "bg_hover": "#5b5a4f",
        "bg_selected": "#a6e22e40",
        "text_primary": "#f8f8f2",
        "text_secondary": "#cfcfc2",
        "text_muted": "#75715e",
        "accent": "#a6e22e",
        "accent_hover": "#c4ff50",
        "accent_dark": "#8bc720",
        "success": "#a6e22e",
        "success_bg": "#a6e22e20",
        "warning": "#e6db74",
        "warning_bg": "#e6db7420",
        "error": "#f92672",
        "error_bg": "#f9267220",
        "border": "#49483e",
        "border_light": "#3e3d32",
        "border_focus": "#a6e22e",
        "header_bg": "#1e1f1a",
        "statusbar_bg": "#1e1f1a",
        "separator": "#49483e",
    },
    
    "cyberpunk": {
        "name": "Cyberpunk",
        "bg_primary": "#0d0221",
        "bg_secondary": "#190535",
        "bg_tertiary": "#240846",
        "bg_input": "#0d0221",
        "bg_hover": "#2f0a57",
        "bg_selected": "#ff00ff40",
        "text_primary": "#00ffff",
        "text_secondary": "#ff00ff",
        "text_muted": "#666699",
        "accent": "#ff00ff",
        "accent_hover": "#ff66ff",
        "accent_dark": "#cc00cc",
        "success": "#00ff00",
        "success_bg": "#00ff0020",
        "warning": "#ffff00",
        "warning_bg": "#ffff0020",
        "error": "#ff0000",
        "error_bg": "#ff000020",
        "border": "#ff00ff",
        "border_light": "#240846",
        "border_focus": "#00ffff",
        "header_bg": "#050112",
        "statusbar_bg": "#050112",
        "separator": "#ff00ff40",
    },
    
    "forest": {
        "name": "Forest",
        "bg_primary": "#1a2f1a",
        "bg_secondary": "#243824",
        "bg_tertiary": "#2e4a2e",
        "bg_input": "#1a2f1a",
        "bg_hover": "#3a5c3a",
        "bg_selected": "#4ade8040",
        "text_primary": "#e8f5e9",
        "text_secondary": "#a5d6a7",
        "text_muted": "#5a7a5a",
        "accent": "#4ade80",
        "accent_hover": "#86efac",
        "accent_dark": "#22c55e",
        "success": "#4ade80",
        "success_bg": "#4ade8020",
        "warning": "#fbbf24",
        "warning_bg": "#fbbf2420",
        "error": "#ef4444",
        "error_bg": "#ef444420",
        "border": "#2e4a2e",
        "border_light": "#243824",
        "border_focus": "#4ade80",
        "header_bg": "#0f1f0f",
        "statusbar_bg": "#0f1f0f",
        "separator": "#2e4a2e",
    },
    
    "ocean": {
        "name": "Ocean",
        "bg_primary": "#0c1821",
        "bg_secondary": "#1b2838",
        "bg_tertiary": "#2a3f54",
        "bg_input": "#0c1821",
        "bg_hover": "#3a5068",
        "bg_selected": "#06b6d440",
        "text_primary": "#e0f2fe",
        "text_secondary": "#7dd3fc",
        "text_muted": "#4a6a7f",
        "accent": "#06b6d4",
        "accent_hover": "#22d3ee",
        "accent_dark": "#0891b2",
        "success": "#10b981",
        "success_bg": "#10b98120",
        "warning": "#f59e0b",
        "warning_bg": "#f59e0b20",
        "error": "#f43f5e",
        "error_bg": "#f43f5e20",
        "border": "#2a3f54",
        "border_light": "#1b2838",
        "border_focus": "#06b6d4",
        "header_bg": "#061018",
        "statusbar_bg": "#061018",
        "separator": "#2a3f54",
    },
    
    # ============================================
    # LIGHT THEMES
    # ============================================
    "light": {
        "name": "Light",
        "bg_primary": "#ffffff",
        "bg_secondary": "#f5f5f5",
        "bg_tertiary": "#e8e8e8",
        "bg_input": "#ffffff",
        "bg_hover": "#e0e0e0",
        "bg_selected": "#2196f340",
        "text_primary": "#212121",
        "text_secondary": "#616161",
        "text_muted": "#9e9e9e",
        "accent": "#2196f3",
        "accent_hover": "#42a5f5",
        "accent_dark": "#1976d2",
        "success": "#4caf50",
        "success_bg": "#4caf5020",
        "warning": "#ff9800",
        "warning_bg": "#ff980020",
        "error": "#f44336",
        "error_bg": "#f4433620",
        "border": "#e0e0e0",
        "border_light": "#eeeeee",
        "border_focus": "#2196f3",
        "header_bg": "#fafafa",
        "statusbar_bg": "#fafafa",
        "separator": "#e0e0e0",
    },
    
    "cream": {
        "name": "Cream",
        "bg_primary": "#faf8f5",
        "bg_secondary": "#f0ece4",
        "bg_tertiary": "#e6e0d4",
        "bg_input": "#faf8f5",
        "bg_hover": "#dcd4c4",
        "bg_selected": "#8b572a40",
        "text_primary": "#3d3d3d",
        "text_secondary": "#666666",
        "text_muted": "#999999",
        "accent": "#8b572a",
        "accent_hover": "#a66b35",
        "accent_dark": "#6f4520",
        "success": "#5a8f5a",
        "success_bg": "#5a8f5a20",
        "warning": "#c9a227",
        "warning_bg": "#c9a22720",
        "error": "#c94a4a",
        "error_bg": "#c94a4a20",
        "border": "#d4cec2",
        "border_light": "#e6e0d4",
        "border_focus": "#8b572a",
        "header_bg": "#f5f2ec",
        "statusbar_bg": "#f5f2ec",
        "separator": "#d4cec2",
    },
    
    "solarized_light": {
        "name": "Solarized Light",
        "bg_primary": "#fdf6e3",
        "bg_secondary": "#eee8d5",
        "bg_tertiary": "#e4ddc8",
        "bg_input": "#fdf6e3",
        "bg_hover": "#d9d2bd",
        "bg_selected": "#268bd240",
        "text_primary": "#073642",
        "text_secondary": "#586e75",
        "text_muted": "#93a1a1",
        "accent": "#268bd2",
        "accent_hover": "#3a9ee0",
        "accent_dark": "#1e6fa8",
        "success": "#859900",
        "success_bg": "#85990020",
        "warning": "#b58900",
        "warning_bg": "#b5890020",
        "error": "#dc322f",
        "error_bg": "#dc322f20",
        "border": "#d9d2bd",
        "border_light": "#eee8d5",
        "border_focus": "#268bd2",
        "header_bg": "#f7f0dd",
        "statusbar_bg": "#f7f0dd",
        "separator": "#d9d2bd",
    },
    
    # ============================================
    # COLORFUL THEMES
    # ============================================
    "purple_haze": {
        "name": "Purple Haze",
        "bg_primary": "#1a1625",
        "bg_secondary": "#2d2640",
        "bg_tertiary": "#3f3659",
        "bg_input": "#1a1625",
        "bg_hover": "#524773",
        "bg_selected": "#a855f740",
        "text_primary": "#f3e8ff",
        "text_secondary": "#c4b5fd",
        "text_muted": "#7c6a9a",
        "accent": "#a855f7",
        "accent_hover": "#c084fc",
        "accent_dark": "#9333ea",
        "success": "#22c55e",
        "success_bg": "#22c55e20",
        "warning": "#eab308",
        "warning_bg": "#eab30820",
        "error": "#ef4444",
        "error_bg": "#ef444420",
        "border": "#3f3659",
        "border_light": "#2d2640",
        "border_focus": "#a855f7",
        "header_bg": "#110f18",
        "statusbar_bg": "#110f18",
        "separator": "#3f3659",
    },
    
    "sunset": {
        "name": "Sunset",
        "bg_primary": "#1f1315",
        "bg_secondary": "#2d1d20",
        "bg_tertiary": "#3d282c",
        "bg_input": "#1f1315",
        "bg_hover": "#4d3338",
        "bg_selected": "#f9732640",
        "text_primary": "#fef2f2",
        "text_secondary": "#fca5a5",
        "text_muted": "#8a5a5a",
        "accent": "#f97316",
        "accent_hover": "#fb923c",
        "accent_dark": "#ea580c",
        "success": "#22c55e",
        "success_bg": "#22c55e20",
        "warning": "#facc15",
        "warning_bg": "#facc1520",
        "error": "#ef4444",
        "error_bg": "#ef444420",
        "border": "#3d282c",
        "border_light": "#2d1d20",
        "border_focus": "#f97316",
        "header_bg": "#150d0f",
        "statusbar_bg": "#150d0f",
        "separator": "#3d282c",
    },
    
    "rose_gold": {
        "name": "Rose Gold",
        "bg_primary": "#1c1517",
        "bg_secondary": "#2a2022",
        "bg_tertiary": "#3a2d30",
        "bg_input": "#1c1517",
        "bg_hover": "#4a3a3e",
        "bg_selected": "#f472b640",
        "text_primary": "#fdf2f8",
        "text_secondary": "#f9a8d4",
        "text_muted": "#8a6070",
        "accent": "#f472b6",
        "accent_hover": "#f9a8d4",
        "accent_dark": "#ec4899",
        "success": "#34d399",
        "success_bg": "#34d39920",
        "warning": "#fbbf24",
        "warning_bg": "#fbbf2420",
        "error": "#fb7185",
        "error_bg": "#fb718520",
        "border": "#3a2d30",
        "border_light": "#2a2022",
        "border_focus": "#f472b6",
        "header_bg": "#120e10",
        "statusbar_bg": "#120e10",
        "separator": "#3a2d30",
    },
    
    "high_contrast": {
        "name": "High Contrast",
        "bg_primary": "#000000",
        "bg_secondary": "#1a1a1a",
        "bg_tertiary": "#2a2a2a",
        "bg_input": "#000000",
        "bg_hover": "#3a3a3a",
        "bg_selected": "#ffff0040",
        "text_primary": "#ffffff",
        "text_secondary": "#cccccc",
        "text_muted": "#888888",
        "accent": "#00ff00",
        "accent_hover": "#33ff33",
        "accent_dark": "#00cc00",
        "success": "#00ff00",
        "success_bg": "#00ff0020",
        "warning": "#ffff00",
        "warning_bg": "#ffff0020",
        "error": "#ff0000",
        "error_bg": "#ff000020",
        "border": "#ffffff",
        "border_light": "#666666",
        "border_focus": "#00ff00",
        "header_bg": "#000000",
        "statusbar_bg": "#000000",
        "separator": "#ffffff",
    },
}

# Theme names for UI display
THEME_NAMES = {key: theme.get("name", key.replace("_", " ").title()) for key, theme in THEMES.items()}


def get_stylesheet(theme_name: str = "dark") -> str:
    """Generate QSS stylesheet for the given theme."""
    
    colors = THEMES.get(theme_name, THEMES["dark"])
    
    return f"""
/* ============================================
   GLOBAL STYLES - Consistent backgrounds
   ============================================ */
QMainWindow, QWidget {{
    background-color: {colors['bg_primary']};
    color: {colors['text_primary']};
    font-family: "Segoe UI", "SF Pro Display", -apple-system, sans-serif;
    font-size: 13px;
}}

/* Scroll areas need transparent content */
QScrollArea > QWidget > QWidget {{
    background-color: {colors['bg_primary']};
}}

/* ============================================
   TAB WIDGET
   ============================================ */
QTabWidget::pane {{
    background-color: {colors['bg_primary']};
    border: none;
}}

QTabBar {{
    background-color: {colors['bg_secondary']};
}}

QTabBar::tab {{
    background-color: {colors['header_bg']};
    color: {colors['text_secondary']};
    padding: 12px 20px;
    margin-right: 2px;
    border: none;
    border-bottom: 3px solid transparent;
    min-width: 80px;
}}

QTabBar::tab:hover {{
    background-color: {colors['bg_tertiary']};
    color: {colors['text_primary']};
}}

QTabBar::tab:selected {{
    background-color: {colors['bg_secondary']};
    color: {colors['accent']};
    border-bottom: 3px solid {colors['accent']};
}}

/* ============================================
   BUTTONS - Better visual distinction
   ============================================ */
QPushButton {{
    background-color: {colors['bg_tertiary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    padding: 8px 16px;
    min-height: 28px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {colors['bg_hover']};
    border-color: {colors['accent']};
}}

QPushButton:pressed {{
    background-color: {colors['border']};
}}

QPushButton:disabled {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_muted']};
    border-color: {colors['border_light']};
}}

QPushButton#primaryButton {{
    background-color: {colors['accent_dark']};
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton#primaryButton:hover {{
    background-color: {colors['accent']};
}}

QPushButton#primaryButton:pressed {{
    background-color: {colors['accent_dark']};
}}

QPushButton#dangerButton {{
    background-color: {colors['error']};
    color: white;
    border: none;
}}

QPushButton#dangerButton:hover {{
    background-color: #ff6b6b;
}}

QPushButton#successButton {{
    background-color: {colors['success']};
    color: white;
    border: none;
}}

/* ============================================
   INPUT FIELDS - Clear boundaries
   ============================================ */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {colors['bg_input']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {colors['accent']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {colors['border_focus']};
    border-width: 2px;
}}

QLineEdit:disabled {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_muted']};
}}

/* ============================================
   COMBO BOXES
   ============================================ */
QComboBox {{
    background-color: {colors['bg_tertiary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 28px;
}}

QComboBox:hover {{
    border-color: {colors['accent']};
}}

QComboBox:focus {{
    border-color: {colors['border_focus']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {colors['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    selection-background-color: {colors['accent_dark']};
    selection-color: white;
    padding: 4px;
}}

/* ============================================
   GROUP BOXES - Visual sections
   ============================================ */
QGroupBox {{
    background-color: {colors['bg_secondary']};
    border: 1px solid {colors['border']};
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 24px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: 4px;
    background-color: {colors['bg_secondary']};
    color: {colors['accent']};
    padding: 2px 8px;
}}

/* ============================================
   FRAMES AND CARDS
   ============================================ */
QFrame {{
    border: none;
}}

QFrame#card {{
    background-color: {colors['bg_secondary']};
    border: 1px solid {colors['border']};
    border-radius: 8px;
    padding: 12px;
}}

QFrame#card:hover {{
    border-color: {colors['accent']};
}}

QFrame#toolbar {{
    background-color: {colors['bg_tertiary']};
    border-bottom: 1px solid {colors['border']};
    padding: 8px;
}}

QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    background-color: {colors['separator']};
    max-width: 1px;
    max-height: 1px;
}}

/* ============================================
   SCROLL BARS
   ============================================ */
QScrollBar:vertical {{
    background-color: {colors['bg_secondary']};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {colors['border']};
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors['text_muted']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {colors['bg_secondary']};
    height: 10px;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors['border']};
    border-radius: 5px;
    min-width: 30px;
    margin: 2px;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

/* ============================================
   TABLES AND TREES
   ============================================ */
QTableWidget, QTreeWidget, QTableView, QTreeView {{
    background-color: {colors['bg_secondary']};
    alternate-background-color: {colors['bg_tertiary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    gridline-color: {colors['border']};
    selection-background-color: {colors['accent_dark']};
    selection-color: white;
}}

QTableWidget::item, QTreeWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {colors['border_light']};
}}

QTableWidget::item:hover, QTreeWidget::item:hover {{
    background-color: {colors['bg_hover']};
}}

QTableWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {colors['accent_dark']};
    color: white;
}}

QHeaderView::section {{
    background-color: {colors['bg_tertiary']};
    color: {colors['text_primary']};
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid {colors['border']};
    font-weight: 600;
}}

QHeaderView::section:hover {{
    background-color: {colors['bg_hover']};
}}

/* ============================================
   PROGRESS BARS
   ============================================ */
QProgressBar {{
    background-color: {colors['bg_tertiary']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {colors['accent']};
    border-radius: 4px;
}}

/* ============================================
   LABELS
   ============================================ */
QLabel {{
    color: {colors['text_primary']};
    background-color: transparent;
}}

QLabel#sectionTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {colors['text_primary']};
    padding: 8px 0;
}}

QLabel#subtitle {{
    color: {colors['text_secondary']};
    font-size: 12px;
}}

QLabel#statusLabel {{
    color: {colors['text_secondary']};
    padding: 4px 8px;
}}

/* ============================================
   LIST WIDGETS
   ============================================ */
QListWidget {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    padding: 4px;
}}

QListWidget::item {{
    padding: 10px 8px;
    border-radius: 4px;
    margin: 2px;
}}

QListWidget::item:hover {{
    background-color: {colors['bg_hover']};
}}

QListWidget::item:selected {{
    background-color: {colors['accent_dark']};
    color: white;
}}

/* ============================================
   CHECKBOXES AND RADIO BUTTONS
   ============================================ */
QCheckBox {{
    color: {colors['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {colors['border']};
    border-radius: 4px;
    background-color: {colors['bg_input']};
}}

QCheckBox::indicator:hover {{
    border-color: {colors['accent']};
}}

QCheckBox::indicator:checked {{
    background-color: {colors['accent']};
    border-color: {colors['accent']};
}}

QRadioButton {{
    color: {colors['text_primary']};
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {colors['border']};
    border-radius: 9px;
    background-color: {colors['bg_input']};
}}

QRadioButton::indicator:checked {{
    background-color: {colors['accent']};
    border-color: {colors['accent']};
}}

/* ============================================
   SPIN BOXES AND SLIDERS
   ============================================ */
QSpinBox, QDoubleSpinBox {{
    background-color: {colors['bg_input']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    padding: 6px;
}}

QSlider::groove:horizontal {{
    height: 6px;
    background-color: {colors['bg_tertiary']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {colors['accent']};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::sub-page:horizontal {{
    background-color: {colors['accent']};
    border-radius: 3px;
}}

/* ============================================
   STATUS BAR - Better spacing
   ============================================ */
QStatusBar {{
    background-color: {colors['statusbar_bg']};
    color: {colors['text_secondary']};
    border-top: 1px solid {colors['border']};
    padding: 4px 8px;
    min-height: 28px;
}}

QStatusBar::item {{
    border: none;
}}

QStatusBar QLabel {{
    padding: 2px 12px;
    color: {colors['text_secondary']};
}}

/* ============================================
   TOOLTIPS
   ============================================ */
QToolTip {{
    background-color: {colors['bg_tertiary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 6px 10px;
}}

/* ============================================
   MENUS
   ============================================ */
QMenuBar {{
    background-color: {colors['header_bg']};
    color: {colors['text_primary']};
    padding: 4px;
}}

QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {colors['bg_tertiary']};
}}

QMenu {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {colors['accent_dark']};
    color: white;
}}

QMenu::separator {{
    height: 1px;
    background-color: {colors['border']};
    margin: 4px 8px;
}}

/* ============================================
   SPLITTERS
   ============================================ */
QSplitter::handle {{
    background-color: {colors['border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* ============================================
   DOCK WIDGETS
   ============================================ */
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {colors['bg_tertiary']};
    padding: 8px;
    border-bottom: 1px solid {colors['border']};
}}

/* ============================================
   TAB WIDGET NESTED (Browser tab)
   ============================================ */
QTabWidget QTabWidget::pane {{
    border: 1px solid {colors['border']};
    border-radius: 6px;
    background-color: {colors['bg_secondary']};
}}

QTabWidget QTabBar::tab {{
    padding: 8px 16px;
    min-width: 60px;
}}
"""


def apply_theme(app: QApplication, theme_name: str = "dark") -> None:
    """Apply theme to the application."""
    stylesheet = get_stylesheet(theme_name)
    app.setStyleSheet(stylesheet)
    logger.info(f"Applied {theme_name} theme")


def get_color(theme_name: str, color_key: str) -> str:
    """Get a specific color from the theme."""
    return THEMES.get(theme_name, THEMES["dark"]).get(color_key, "#ffffff")
