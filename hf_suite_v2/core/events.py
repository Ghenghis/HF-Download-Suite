"""
Event bus system for decoupled component communication.
"""

from collections import defaultdict
from typing import Callable, Any
import threading
import logging

logger = logging.getLogger(__name__)


class Events:
    """Event name constants."""
    
    # Download events
    DOWNLOAD_QUEUED = "download.queued"
    DOWNLOAD_STARTED = "download.started"
    DOWNLOAD_PROGRESS = "download.progress"
    DOWNLOAD_COMPLETED = "download.completed"
    DOWNLOAD_FAILED = "download.failed"
    DOWNLOAD_CANCELLED = "download.cancelled"
    DOWNLOAD_PAUSED = "download.paused"
    DOWNLOAD_RESUMED = "download.resumed"
    
    # Queue events
    QUEUE_CHANGED = "queue.changed"
    QUEUE_CLEARED = "queue.cleared"
    
    # UI events
    THEME_CHANGED = "ui.theme_changed"
    TAB_CHANGED = "ui.tab_changed"
    NOTIFICATION = "ui.notification"
    STATUS_UPDATE = "ui.status_update"
    
    # Settings events
    SETTINGS_CHANGED = "settings.changed"
    PROFILE_CHANGED = "settings.profile_changed"
    TOKEN_UPDATED = "settings.token_updated"
    
    # Model events
    MODEL_SCANNED = "model.scanned"
    MODEL_DELETED = "model.deleted"
    SCAN_STARTED = "model.scan_started"
    SCAN_COMPLETED = "model.scan_completed"
    
    # History events
    HISTORY_ADDED = "history.added"
    HISTORY_CLEARED = "history.cleared"
    FAVORITE_TOGGLED = "history.favorite_toggled"


class EventBus:
    """
    Thread-safe singleton event bus for application-wide communication.
    
    Usage:
        bus = EventBus()
        bus.subscribe(Events.DOWNLOAD_COMPLETED, my_handler)
        bus.emit(Events.DOWNLOAD_COMPLETED, download_id=123, path="/path")
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._subscribers = defaultdict(list)
                    cls._instance._subscriber_lock = threading.Lock()
        return cls._instance
    
    def subscribe(self, event: str, callback: Callable) -> None:
        """
        Subscribe to an event.
        
        Args:
            event: Event name from Events class
            callback: Function to call when event is emitted
        """
        with self._subscriber_lock:
            if callback not in self._subscribers[event]:
                self._subscribers[event].append(callback)
                logger.debug(f"Subscribed to {event}: {callback.__name__}")
    
    def unsubscribe(self, event: str, callback: Callable) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event: Event name
            callback: Previously subscribed callback
        """
        with self._subscriber_lock:
            if callback in self._subscribers[event]:
                self._subscribers[event].remove(callback)
                logger.debug(f"Unsubscribed from {event}: {callback.__name__}")
    
    def emit(self, event: str, *args, **kwargs) -> None:
        """
        Emit an event to all subscribers.
        
        Args:
            event: Event name
            *args, **kwargs: Arguments to pass to callbacks
        """
        with self._subscriber_lock:
            callbacks = list(self._subscribers[event])
        
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in event handler {callback.__name__} for {event}: {e}")
    
    def emit_async(self, event: str, *args, **kwargs) -> threading.Thread:
        """
        Emit an event asynchronously in a new thread.
        
        Returns:
            Thread object for the async emission
        """
        thread = threading.Thread(
            target=self.emit,
            args=(event, *args),
            kwargs=kwargs,
            daemon=True
        )
        thread.start()
        return thread
    
    def clear(self, event: str = None) -> None:
        """
        Clear subscribers for an event or all events.
        
        Args:
            event: Specific event to clear, or None for all
        """
        with self._subscriber_lock:
            if event:
                self._subscribers[event].clear()
            else:
                self._subscribers.clear()
    
    def get_subscriber_count(self, event: str) -> int:
        """Get number of subscribers for an event."""
        with self._subscriber_lock:
            return len(self._subscribers[event])


# Convenience function
def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return EventBus()
