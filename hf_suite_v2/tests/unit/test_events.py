"""
Tests for event bus system.
"""

import pytest
import threading
import time

from hf_suite_v2.core.events import EventBus, Events, get_event_bus


class TestEventBus:
    """Tests for EventBus."""
    
    def test_singleton(self):
        """Test that EventBus is a singleton."""
        bus1 = EventBus()
        bus2 = EventBus()
        assert bus1 is bus2
    
    def test_get_event_bus(self):
        """Test get_event_bus convenience function."""
        bus = get_event_bus()
        assert isinstance(bus, EventBus)
        assert bus is EventBus()
    
    def test_subscribe_emit(self):
        """Test basic subscribe and emit."""
        bus = EventBus()
        bus.clear()  # Start fresh
        
        received = []
        
        def handler(data):
            received.append(data)
        
        bus.subscribe("test.event", handler)
        bus.emit("test.event", "test_data")
        
        assert len(received) == 1
        assert received[0] == "test_data"
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event."""
        bus = EventBus()
        bus.clear()
        
        results = []
        
        def handler1(val):
            results.append(f"h1:{val}")
        
        def handler2(val):
            results.append(f"h2:{val}")
        
        bus.subscribe("multi.event", handler1)
        bus.subscribe("multi.event", handler2)
        bus.emit("multi.event", "data")
        
        assert len(results) == 2
        assert "h1:data" in results
        assert "h2:data" in results
    
    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        bus.clear()
        
        calls = []
        
        def handler():
            calls.append(1)
        
        bus.subscribe("unsub.test", handler)
        bus.emit("unsub.test")
        assert len(calls) == 1
        
        bus.unsubscribe("unsub.test", handler)
        bus.emit("unsub.test")
        assert len(calls) == 1  # Should not increase
    
    def test_emit_with_kwargs(self):
        """Test emit with keyword arguments."""
        bus = EventBus()
        bus.clear()
        
        received = {}
        
        def handler(**kwargs):
            received.update(kwargs)
        
        bus.subscribe("kwargs.event", handler)
        bus.emit("kwargs.event", task_id=123, status="completed")
        
        assert received["task_id"] == 123
        assert received["status"] == "completed"
    
    def test_subscriber_count(self):
        """Test get_subscriber_count."""
        bus = EventBus()
        bus.clear()
        
        def handler1(): pass
        def handler2(): pass
        
        assert bus.get_subscriber_count("count.test") == 0
        
        bus.subscribe("count.test", handler1)
        assert bus.get_subscriber_count("count.test") == 1
        
        bus.subscribe("count.test", handler2)
        assert bus.get_subscriber_count("count.test") == 2
    
    def test_clear_specific_event(self):
        """Test clearing specific event."""
        bus = EventBus()
        bus.clear()
        
        def handler(): pass
        
        bus.subscribe("event1", handler)
        bus.subscribe("event2", handler)
        
        bus.clear("event1")
        
        assert bus.get_subscriber_count("event1") == 0
        assert bus.get_subscriber_count("event2") == 1
    
    def test_handler_exception(self):
        """Test that handler exceptions don't break other handlers."""
        bus = EventBus()
        bus.clear()
        
        results = []
        
        def bad_handler():
            raise ValueError("test error")
        
        def good_handler():
            results.append("success")
        
        bus.subscribe("error.test", bad_handler)
        bus.subscribe("error.test", good_handler)
        
        # Should not raise, and good_handler should still run
        bus.emit("error.test")
        
        assert "success" in results
    
    def test_no_duplicate_subscribe(self):
        """Test that same handler isn't subscribed twice."""
        bus = EventBus()
        bus.clear()
        
        calls = []
        
        def handler():
            calls.append(1)
        
        bus.subscribe("dup.test", handler)
        bus.subscribe("dup.test", handler)  # Second subscribe
        
        bus.emit("dup.test")
        
        assert len(calls) == 1  # Should only be called once


class TestEvents:
    """Tests for Events constants."""
    
    def test_download_events_exist(self):
        """Test download event constants exist."""
        assert hasattr(Events, "DOWNLOAD_QUEUED")
        assert hasattr(Events, "DOWNLOAD_STARTED")
        assert hasattr(Events, "DOWNLOAD_PROGRESS")
        assert hasattr(Events, "DOWNLOAD_COMPLETED")
        assert hasattr(Events, "DOWNLOAD_FAILED")
    
    def test_ui_events_exist(self):
        """Test UI event constants exist."""
        assert hasattr(Events, "THEME_CHANGED")
        assert hasattr(Events, "TAB_CHANGED")
        assert hasattr(Events, "NOTIFICATION")
    
    def test_event_values_unique(self):
        """Test that event values are unique."""
        events = [
            Events.DOWNLOAD_QUEUED,
            Events.DOWNLOAD_STARTED,
            Events.DOWNLOAD_COMPLETED,
            Events.DOWNLOAD_FAILED,
            Events.QUEUE_CHANGED,
        ]
        assert len(events) == len(set(events))
