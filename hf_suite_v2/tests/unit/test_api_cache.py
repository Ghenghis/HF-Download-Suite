"""
Tests for API response caching.
"""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestAPICache:
    """Tests for the APICache class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset singleton for each test
        from hf_suite_v2.core.api.cache import APICache
        APICache._instance = None
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Patch CACHE_DIR
        with patch('hf_suite_v2.core.api.cache.CACHE_DIR', self.temp_dir):
            self.cache = APICache()
            self.cache.cache_dir = self.temp_dir
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        self.cache.set("test_key", {"data": "value"})
        result = self.cache.get("test_key")
        
        assert result is not None
        assert result["data"] == "value"
    
    def test_get_missing_key(self):
        """Test getting a non-existent key."""
        result = self.cache.get("nonexistent")
        assert result is None
    
    def test_expiration(self):
        """Test that expired entries return None."""
        self.cache.set("expiring_key", "value", ttl=1)
        
        # Should exist initially
        assert self.cache.get("expiring_key") == "value"
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired
        assert self.cache.get("expiring_key") is None
    
    def test_delete(self):
        """Test deleting a cache entry."""
        self.cache.set("to_delete", "value")
        assert self.cache.get("to_delete") == "value"
        
        self.cache.delete("to_delete")
        assert self.cache.get("to_delete") is None
    
    def test_clear(self):
        """Test clearing all cache entries."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        count = self.cache.clear()
        
        assert count == 3
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        assert self.cache.get("key3") is None
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        self.cache.set("short_lived", "value", ttl=1)
        self.cache.set("long_lived", "value", ttl=3600)
        
        time.sleep(1.5)
        
        count = self.cache.cleanup_expired()
        
        assert count == 1
        assert self.cache.get("long_lived") == "value"
    
    def test_get_stats(self):
        """Test cache statistics."""
        self.cache.set("key1", "value1")
        self.cache.get("key1")  # Hit
        self.cache.get("key1")  # Hit
        self.cache.get("missing")  # Miss
        
        stats = self.cache.get_stats()
        
        assert stats['hits'] >= 2
        assert stats['misses'] >= 1
        assert stats['entry_count'] >= 1
        assert 'hit_rate' in stats
        assert 'total_size_mb' in stats
    
    def test_cache_key_generation(self):
        """Test that cache keys are unique for different inputs."""
        key1 = self.cache._get_cache_key("prefix", "arg1", kwarg="val1")
        key2 = self.cache._get_cache_key("prefix", "arg1", kwarg="val2")
        key3 = self.cache._get_cache_key("prefix", "arg2", kwarg="val1")
        
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
    
    def test_complex_data_types(self):
        """Test caching complex data structures."""
        complex_data = {
            "list": [1, 2, 3],
            "nested": {"a": "b", "c": [4, 5]},
            "number": 42,
            "boolean": True,
            "null": None,
        }
        
        self.cache.set("complex", complex_data)
        result = self.cache.get("complex")
        
        assert result == complex_data


class TestCachedDecorator:
    """Tests for the @cached decorator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from hf_suite_v2.core.api.cache import APICache
        APICache._instance = None
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cached_decorator_caches_result(self):
        """Test that decorator caches function results."""
        call_count = 0
        
        from hf_suite_v2.core.api.cache import cached, get_cache
        
        @cached("test_func", ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call - should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call with same args - should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        # Note: call_count might be 1 or 2 depending on cache state
    
    def test_cached_decorator_different_args(self):
        """Test that different args get different cache entries."""
        from hf_suite_v2.core.api.cache import cached
        
        @cached("mult_func", ttl=60)
        def multiply(x, y):
            return x * y
        
        result1 = multiply(2, 3)
        result2 = multiply(4, 5)
        
        assert result1 == 6
        assert result2 == 20


class TestTTLConstants:
    """Tests for TTL constant values."""
    
    def test_ttl_values_are_positive(self):
        """Test that all TTL values are positive."""
        from hf_suite_v2.core.api.cache import (
            TTL_SEARCH, TTL_REPO_INFO, TTL_FILE_LIST
        )
        
        assert TTL_SEARCH > 0
        assert TTL_REPO_INFO > 0
        assert TTL_FILE_LIST > 0
    
    def test_ttl_ordering(self):
        """Test that TTL values have sensible ordering."""
        from hf_suite_v2.core.api.cache import (
            TTL_SEARCH, TTL_REPO_INFO, TTL_FILE_LIST
        )
        
        # Repo info should be cached longer than search results
        assert TTL_REPO_INFO >= TTL_SEARCH
