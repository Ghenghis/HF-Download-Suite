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

# Theme color definitions - Enhanced with better contrast
THEMES = {
    "dark": {
        # Backgrounds - More contrast between levels
        "bg_primary": "#0d1117",      # Darkest - main background
        "bg_secondary": "#161b22",    # Cards and panels
        "bg_tertiary": "#21262d",     # Elevated elements
        "bg_input": "#0d1117",        # Input fields
        "bg_hover": "#30363d",        # Hover states
        "bg_selected": "#1f6feb20",   # Selected items
        
        # Text - Clear hierarchy
        "text_primary": "#e6edf3",    # Main text
        "text_secondary": "#8b949e",  # Secondary text
        "text_muted": "#6e7681",      # Muted/disabled text
        
        # Accent colors
        "accent": "#58a6ff",          # Primary accent
        "accent_hover": "#79c0ff",    # Accent hover
        "accent_dark": "#1f6feb",     # Darker accent for backgrounds
        
        # Status colors
        "success": "#3fb950",
        "success_bg": "#23863620",
        "warning": "#d29922",
        "warning_bg": "#d2992220",
        "error": "#f85149",
        "error_bg": "#f8514920",
        
        # Borders - Visible but subtle
        "border": "#30363d",
        "border_light": "#21262d",
        "border_focus": "#58a6ff",
        
        # Special
        "header_bg": "#010409",       # Tab bar, toolbar backgrounds
        "statusbar_bg": "#010409",    # Status bar
        "separator": "#30363d",       # Separators
    },
    "light": {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f6f8fa",
        "bg_tertiary": "#eaeef2",
        "bg_input": "#ffffff",
        "bg_hover": "#eaeef2",
        "bg_selected": "#ddf4ff",
        "text_primary": "#1f2328",
        "text_secondary": "#656d76",
        "text_muted": "#8c959f",
        "accent": "#0969da",
        "accent_hover": "#0550ae",
        "accent_dark": "#0969da",
        "success": "#1a7f37",
        "success_bg": "#dafbe1",
        "warning": "#9a6700",
        "warning_bg": "#fff8c5",
        "error": "#cf222e",
        "error_bg": "#ffebe9",
        "border": "#d0d7de",
        "border_light": "#eaeef2",
        "border_focus": "#0969da",
        "header_bg": "#f6f8fa",
        "statusbar_bg": "#f6f8fa",
        "separator": "#d0d7de",
    },
}


def get_stylesheet(theme_name: str = "dark") -> str:
    """Generate QSS stylesheet for the given theme."""
    
    colors = THEMES.get(theme_name, THEMES["dark"])
    
    return f"""
/* ============================================
   GLOBAL STYLES
   ============================================ */
QMainWindow {{
    background-color: {colors['bg_primary']};
    color: {colors['text_primary']};
}}

QWidget {{
    background-color: transparent;
    color: {colors['text_primary']};
    font-family: "Segoe UI", "SF Pro Display", -apple-system, sans-serif;
    font-size: 13px;
}}

/* ============================================
   TAB WIDGET - Enhanced contrast
   ============================================ */
QTabWidget::pane {{
    border: none;
    background-color: {colors['bg_primary']};
    border-top: 1px solid {colors['border']};
}}

QTabBar {{
    background-color: {colors['header_bg']};
    qproperty-drawBase: 0;
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
