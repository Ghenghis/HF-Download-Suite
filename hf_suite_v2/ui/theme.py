"""
Theme management and QSS styling.
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

# Theme color definitions
THEMES = {
    "dark": {
        "bg_primary": "#1e1e2e",
        "bg_secondary": "#313244",
        "bg_tertiary": "#45475a",
        "bg_hover": "#585b70",
        "text_primary": "#cdd6f4",
        "text_secondary": "#a6adc8",
        "text_muted": "#7f849c",
        "accent": "#89b4fa",
        "accent_hover": "#b4befe",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
        "error": "#f38ba8",
        "border": "#585b70",
        "border_light": "#45475a",
    },
    "light": {
        "bg_primary": "#eff1f5",
        "bg_secondary": "#e6e9ef",
        "bg_tertiary": "#dce0e8",
        "bg_hover": "#ccd0da",
        "text_primary": "#4c4f69",
        "text_secondary": "#5c5f77",
        "text_muted": "#8c8fa1",
        "accent": "#1e66f5",
        "accent_hover": "#7287fd",
        "success": "#40a02b",
        "warning": "#df8e1d",
        "error": "#d20f39",
        "border": "#ccd0da",
        "border_light": "#dce0e8",
    },
}


def get_stylesheet(theme_name: str = "dark") -> str:
    """Generate QSS stylesheet for the given theme."""
    
    colors = THEMES.get(theme_name, THEMES["dark"])
    
    return f"""
/* Global styles */
QMainWindow, QWidget {{
    background-color: {colors['bg_primary']};
    color: {colors['text_primary']};
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}

/* Tab widget */
QTabWidget::pane {{
    border: none;
    background-color: {colors['bg_primary']};
}}

QTabBar {{
    background-color: {colors['bg_secondary']};
}}

QTabBar::tab {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_secondary']};
    padding: 12px 24px;
    border: none;
    border-bottom: 3px solid transparent;
    min-width: 100px;
}}

QTabBar::tab:hover {{
    background-color: {colors['bg_tertiary']};
    color: {colors['text_primary']};
}}

QTabBar::tab:selected {{
    background-color: {colors['bg_primary']};
    color: {colors['accent']};
    border-bottom-color: {colors['accent']};
}}

/* Buttons */
QPushButton {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    padding: 8px 16px;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {colors['bg_tertiary']};
    border-color: {colors['accent']};
}}

QPushButton:pressed {{
    background-color: {colors['bg_hover']};
}}

QPushButton:disabled {{
    background-color: {colors['bg_tertiary']};
    color: {colors['text_muted']};
    border-color: {colors['border_light']};
}}

QPushButton#primaryButton {{
    background-color: {colors['accent']};
    color: {colors['bg_primary']};
    border: none;
}}

QPushButton#primaryButton:hover {{
    background-color: {colors['accent_hover']};
}}

QPushButton#dangerButton {{
    background-color: {colors['error']};
    color: white;
    border: none;
}}

/* Input fields */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {colors['accent']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {colors['accent']};
}}

QLineEdit:disabled {{
    background-color: {colors['bg_tertiary']};
    color: {colors['text_muted']};
}}

/* Combo boxes */
QComboBox {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 32px;
}}

QComboBox:hover {{
    border-color: {colors['accent']};
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
    selection-background-color: {colors['accent']};
}}

/* Scroll bars */
QScrollBar:vertical {{
    background-color: {colors['bg_secondary']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {colors['border']};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors['text_muted']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {colors['bg_secondary']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors['border']};
    border-radius: 6px;
    min-width: 30px;
}}

/* Progress bar */
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

/* Labels */
QLabel {{
    color: {colors['text_primary']};
}}

QLabel#sectionTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {colors['text_primary']};
}}

QLabel#subtitle {{
    color: {colors['text_secondary']};
    font-size: 12px;
}}

/* Frames and cards */
QFrame#card {{
    background-color: {colors['bg_secondary']};
    border: 1px solid {colors['border_light']};
    border-radius: 8px;
}}

QFrame#card:hover {{
    border-color: {colors['accent']};
}}

/* List widgets */
QListWidget {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:hover {{
    background-color: {colors['bg_tertiary']};
}}

QListWidget::item:selected {{
    background-color: {colors['accent']};
    color: {colors['bg_primary']};
}}

/* Checkboxes */
QCheckBox {{
    color: {colors['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {colors['border']};
    border-radius: 4px;
    background-color: {colors['bg_secondary']};
}}

QCheckBox::indicator:hover {{
    border-color: {colors['accent']};
}}

QCheckBox::indicator:checked {{
    background-color: {colors['accent']};
    border-color: {colors['accent']};
}}

/* Tooltips */
QToolTip {{
    background-color: {colors['bg_tertiary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}

/* Status bar */
QStatusBar {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_secondary']};
    border-top: 1px solid {colors['border_light']};
}}

/* Menu */
QMenuBar {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
}}

QMenuBar::item:selected {{
    background-color: {colors['bg_tertiary']};
}}

QMenu {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
}}

QMenu::item:selected {{
    background-color: {colors['accent']};
    color: {colors['bg_primary']};
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
