"""
Application setup and entry point.
"""

import sys
import os
import platform
import logging

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

from ..core import setup_logging, get_config
from ..core.download import get_download_manager
from ..core.constants import APP_NAME, APP_VERSION
from .main_window import MainWindow

logger = logging.getLogger(__name__)


def setup_environment() -> None:
    """Configure environment variables for Qt."""
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"


def get_icon_path() -> str:
    """Get the appropriate icon path based on platform."""
    system = platform.system().lower()
    base_path = os.path.dirname(os.path.dirname(__file__))
    assets_path = os.path.join(base_path, "assets", "icons")
    
    if system == "darwin":
        return os.path.join(assets_path, "icon.icns")
    elif system == "windows":
        return os.path.join(assets_path, "icon.ico")
    else:
        return os.path.join(assets_path, "icon.png")


def create_app(args: list = None) -> tuple:
    """
    Create and configure the application.
    
    Returns:
        Tuple of (QApplication, MainWindow)
    """
    setup_environment()
    setup_logging()
    
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    # Create application
    app = QApplication(args or sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Set icon
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Load config
    config = get_config()
    
    # Apply theme
    from .theme import apply_theme
    apply_theme(app, config.ui.theme)
    
    # Create main window
    window = MainWindow()
    
    # Restore window geometry
    if config.ui.remember_window_size:
        window.resize(config.ui.window_width, config.ui.window_height)
        if config.ui.window_x is not None and config.ui.window_y is not None:
            window.move(config.ui.window_x, config.ui.window_y)
    
    # Start download manager
    manager = get_download_manager()
    manager.start()
    
    return app, window


def create_system_tray(app: QApplication, window: MainWindow) -> QSystemTrayIcon:
    """
    Create system tray icon with context menu.
    
    Args:
        app: The QApplication instance
        window: The main window instance
        
    Returns:
        QSystemTrayIcon instance
    """
    # Check if system tray is available
    if not QSystemTrayIcon.isSystemTrayAvailable():
        logger.warning("System tray not available on this system")
        return None
    
    # Create tray icon
    tray = QSystemTrayIcon(app)
    
    # Set icon
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        tray.setIcon(QIcon(icon_path))
    else:
        tray.setIcon(app.windowIcon())
    
    tray.setToolTip(f"{APP_NAME} v{APP_VERSION}")
    
    # Create context menu
    menu = QMenu()
    
    # Show/Hide action
    show_action = QAction("Show/Hide", app)
    show_action.triggered.connect(lambda: window.hide() if window.isVisible() else window.show())
    menu.addAction(show_action)
    
    menu.addSeparator()
    
    # Download controls
    manager = get_download_manager()
    
    pause_action = QAction("Pause All", app)
    pause_action.triggered.connect(manager.pause_all)
    menu.addAction(pause_action)
    
    resume_action = QAction("Resume All", app)
    resume_action.triggered.connect(manager.resume_all)
    menu.addAction(resume_action)
    
    menu.addSeparator()
    
    # Quit action
    quit_action = QAction("Quit", app)
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)
    
    tray.setContextMenu(menu)
    
    # Double-click to show window
    tray.activated.connect(lambda reason: window.show() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
    
    return tray


def run_app() -> int:
    """Run the application and return exit code."""
    try:
        app, window = create_app()
        
        # Create system tray
        config = get_config()
        tray = None
        if config.ui.minimize_to_tray:
            tray = create_system_tray(app, window)
            if tray:
                tray.show()
        
        window.show()
        
        exit_code = app.exec()
        
        # Cleanup
        manager = get_download_manager()
        manager.stop()
        
        # Save window geometry
        config = get_config()
        if config.ui.remember_window_size:
            config.update(
                **{
                    "ui.window_width": window.width(),
                    "ui.window_height": window.height(),
                    "ui.window_x": window.x(),
                    "ui.window_y": window.y(),
                }
            )
        
        logger.info("Application exited normally")
        return exit_code
        
    except Exception as e:
        logger.exception(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_app())
