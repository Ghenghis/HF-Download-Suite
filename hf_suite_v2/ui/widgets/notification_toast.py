"""
Toast notification widget for non-intrusive user feedback.

Displays temporary notifications that automatically fade out,
supporting different notification levels (success, warning, error, info).
"""

import logging
from typing import Optional
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QPushButton,
    QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QPoint
)
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Notification severity levels."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


# Style configurations for each notification type
NOTIFICATION_STYLES = {
    NotificationType.SUCCESS: {
        "background": "#a6e3a1",
        "text": "#1e1e2e",
        "icon": "✓",
        "border": "#94e2a0",
    },
    NotificationType.WARNING: {
        "background": "#fab387",
        "text": "#1e1e2e",
        "icon": "⚠",
        "border": "#f9a875",
    },
    NotificationType.ERROR: {
        "background": "#f38ba8",
        "text": "#1e1e2e",
        "icon": "✕",
        "border": "#f17a9a",
    },
    NotificationType.INFO: {
        "background": "#89b4fa",
        "text": "#1e1e2e",
        "icon": "ℹ",
        "border": "#7aa8f9",
    },
}


class NotificationToast(QWidget):
    """
    A toast notification widget that appears temporarily.
    
    Features:
    - Auto-dismiss after configurable duration
    - Fade-in and fade-out animations
    - Different styles for success, warning, error, info
    - Optional close button
    - Stackable notifications
    
    Usage:
        toast = NotificationToast(
            message="Download complete!",
            notification_type=NotificationType.SUCCESS,
            duration=3000,
            parent=self
        )
        toast.show()
    """
    
    # Signal emitted when toast is closed
    closed = pyqtSignal()
    
    def __init__(
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        duration: int = 5000,
        show_close: bool = True,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the toast notification.
        
        Args:
            message: The message to display
            notification_type: Type/severity of notification
            duration: Auto-dismiss duration in milliseconds (0 = no auto-dismiss)
            show_close: Whether to show close button
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        
        self._setup_ui(show_close)
        self._setup_animation()
        
        if duration > 0:
            self._setup_auto_dismiss()
    
    def _setup_ui(self, show_close: bool) -> None:
        """Set up the toast UI."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Get style for this notification type
        style = NOTIFICATION_STYLES[self.notification_type]
        
        # Apply container style
        self.setStyleSheet(f"""
            NotificationToast {{
                background-color: {style['background']};
                border: 2px solid {style['border']};
                border-radius: 8px;
            }}
        """)
        
        # Icon label
        icon_label = QLabel(style['icon'])
        icon_label.setStyleSheet(f"color: {style['text']}; font-size: 18px;")
        layout.addWidget(icon_label)
        
        # Message label
        message_label = QLabel(self.message)
        message_label.setStyleSheet(f"color: {style['text']}; font-size: 13px;")
        message_label.setWordWrap(True)
        message_label.setMaximumWidth(400)
        layout.addWidget(message_label, 1)
        
        # Close button
        if show_close:
            close_btn = QPushButton("×")
            close_btn.setFixedSize(24, 24)
            close_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {style['text']};
                    border: none;
                    font-size: 18px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: rgba(0, 0, 0, 0.1);
                    border-radius: 12px;
                }}
            """)
            close_btn.clicked.connect(self.dismiss)
            layout.addWidget(close_btn)
        
        # Set up opacity effect for animations
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.adjustSize()
    
    def _setup_animation(self) -> None:
        """Set up fade animations."""
        # Fade in animation
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Fade out animation
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out.finished.connect(self._on_fade_out_finished)
    
    def _setup_auto_dismiss(self) -> None:
        """Set up auto-dismiss timer."""
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.dismiss)
    
    def show(self) -> None:
        """Show the toast with fade-in animation."""
        super().show()
        self.fade_in.start()
        
        if self.duration > 0:
            self.dismiss_timer.start(self.duration)
    
    def dismiss(self) -> None:
        """Dismiss the toast with fade-out animation."""
        if hasattr(self, 'dismiss_timer'):
            self.dismiss_timer.stop()
        
        self.fade_out.start()
    
    def _on_fade_out_finished(self) -> None:
        """Handle fade out completion."""
        self.closed.emit()
        self.close()
        self.deleteLater()


class NotificationManager:
    """
    Manages toast notifications for an application window.
    
    Handles stacking multiple notifications and positioning them
    relative to the parent window.
    
    Usage:
        manager = NotificationManager(main_window)
        manager.show_success("File saved!")
        manager.show_error("Download failed")
    """
    
    def __init__(self, parent: QWidget):
        """
        Initialize the notification manager.
        
        Args:
            parent: The parent widget (usually main window)
        """
        self.parent = parent
        self.active_toasts: list[NotificationToast] = []
        self.toast_spacing = 10
        self.margin_right = 20
        self.margin_top = 20
    
    def _calculate_position(self, toast: NotificationToast) -> QPoint:
        """Calculate position for a new toast."""
        parent_rect = self.parent.geometry()
        
        # Start from top-right corner
        x = parent_rect.right() - toast.width() - self.margin_right
        y = parent_rect.top() + self.margin_top
        
        # Stack below existing toasts
        for existing in self.active_toasts:
            if existing.isVisible():
                y += existing.height() + self.toast_spacing
        
        return QPoint(x, y)
    
    def _on_toast_closed(self, toast: NotificationToast) -> None:
        """Handle toast closed."""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
    
    def show(
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        duration: int = 5000
    ) -> NotificationToast:
        """
        Show a notification toast.
        
        Args:
            message: Message to display
            notification_type: Type of notification
            duration: Auto-dismiss duration in ms
            
        Returns:
            The created toast widget
        """
        toast = NotificationToast(
            message=message,
            notification_type=notification_type,
            duration=duration,
            parent=None  # Top-level window
        )
        
        # Position the toast
        pos = self._calculate_position(toast)
        toast.move(pos)
        
        # Track and show
        self.active_toasts.append(toast)
        toast.closed.connect(lambda: self._on_toast_closed(toast))
        toast.show()
        
        return toast
    
    def show_success(self, message: str, duration: int = 5000) -> NotificationToast:
        """Show a success notification."""
        return self.show(message, NotificationType.SUCCESS, duration)
    
    def show_warning(self, message: str, duration: int = 5000) -> NotificationToast:
        """Show a warning notification."""
        return self.show(message, NotificationType.WARNING, duration)
    
    def show_error(self, message: str, duration: int = 8000) -> NotificationToast:
        """Show an error notification (longer duration by default)."""
        return self.show(message, NotificationType.ERROR, duration)
    
    def show_info(self, message: str, duration: int = 5000) -> NotificationToast:
        """Show an info notification."""
        return self.show(message, NotificationType.INFO, duration)
    
    def clear_all(self) -> None:
        """Dismiss all active toasts."""
        for toast in self.active_toasts[:]:
            toast.dismiss()
