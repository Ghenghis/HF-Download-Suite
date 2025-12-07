"""
Unit tests for API wrappers and base classes.

Tests API error handling, caching, and configuration
without requiring network access.
"""

import pytest
from pathlib import Path


class TestAPIBase:
    """Tests for base API functionality."""
    
    def test_api_error_class(self):
        """Test APIError exception class."""
        from hf_suite_v2.core.api.base import APIError
        
        error = APIError("Test error message")
        assert str(error) == "Test error message"
    
    def test_api_error_with_status_code(self):
        """Test APIError with status code."""
        from hf_suite_v2.core.api.base import APIError
        
        error = APIError("Not found", status_code=404)
        assert error.status_code == 404
    
    def test_api_error_inheritance(self):
        """Test APIError inherits from Exception."""
        from hf_suite_v2.core.api.base import APIError
        
        assert issubclass(APIError, Exception)
    
    def test_api_classes_importable(self):
        """Test that API classes are importable."""
        from hf_suite_v2.core.api import (
            HuggingFaceAPI,
            ModelScopeAPI,
            BaseAPI,
            APIError
        )
        
        assert HuggingFaceAPI is not None
        assert ModelScopeAPI is not None


class TestAPICaching:
    """Tests for API response caching."""
    
    def test_cache_singleton(self):
        """Test cache is a singleton."""
        from hf_suite_v2.core.api.cache import get_cache
        
        cache1 = get_cache()
        cache2 = get_cache()
        
        # Should be the same instance (singleton)
        assert cache1 is cache2
    
    def test_cached_search_results(self):
        """Test that search results can be cached."""
        from hf_suite_v2.core.api.cache import get_cache
        
        cache = get_cache()
        
        # Simulate caching a search result
        cache.set("api_test:search_query", [{"id": "test/model"}], ttl=1800)
        
        result = cache.get("api_test:search_query")
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == "test/model"
    
    def test_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        from hf_suite_v2.core.api.cache import get_cache
        
        cache = get_cache()
        result = cache.get("definitely_nonexistent_key_xyz123abc")
        
        assert result is None
    
    def test_cache_stats_structure(self):
        """Test that cache stats have correct structure."""
        from hf_suite_v2.core.api.cache import get_cache
        
        cache = get_cache()
        stats = cache.get_stats()
        
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'hit_rate' in stats
        assert 'entry_count' in stats
        assert 'total_size_mb' in stats
    
    def test_cache_ttl_constants(self):
        """Test TTL constants exist and are valid."""
        from hf_suite_v2.core.api.cache import (
            TTL_SEARCH, TTL_REPO_INFO, TTL_FILE_LIST
        )
        
        assert TTL_SEARCH > 0
        assert TTL_REPO_INFO > 0
        assert TTL_FILE_LIST > 0
    
    def test_cache_delete(self):
        """Test cache entry deletion."""
        from hf_suite_v2.core.api.cache import get_cache
        
        cache = get_cache()
        
        cache.set("api_test:to_delete", "value")
        assert cache.get("api_test:to_delete") == "value"
        
        cache.delete("api_test:to_delete")
        assert cache.get("api_test:to_delete") is None


class TestAPIConfiguration:
    """Tests for API-related configuration."""
    
    def test_network_settings_exist(self):
        """Test network settings in config."""
        from hf_suite_v2.core import get_config
        
        config = get_config()
        
        assert hasattr(config.network, 'timeout')
        assert hasattr(config.network, 'hf_endpoint')
        assert hasattr(config.network, 'use_hf_mirror')
    
    def test_network_timeout_positive(self):
        """Test network timeout is positive."""
        from hf_suite_v2.core import get_config
        
        config = get_config()
        
        assert config.network.timeout > 0
    
    def test_hf_endpoint_is_url(self):
        """Test HF endpoint looks like a URL."""
        from hf_suite_v2.core import get_config
        
        config = get_config()
        
        endpoint = config.network.hf_endpoint
        assert endpoint.startswith("http")


class TestAPIRetryConfig:
    """Tests for API retry configuration."""
    
    def test_retry_settings_exist(self):
        """Test retry settings in config."""
        from hf_suite_v2.core import get_config
        
        config = get_config()
        
        assert hasattr(config.download, 'auto_retry')
        assert hasattr(config.download, 'max_retries')
        assert hasattr(config.download, 'retry_delay')
    
    def test_max_retries_range(self):
        """Test max retries is within valid range."""
        from hf_suite_v2.core import get_config
        
        config = get_config()
        
        assert 0 <= config.download.max_retries <= 10
    
    def test_retry_delay_positive(self):
        """Test retry delay is positive."""
        from hf_suite_v2.core import get_config
        
        config = get_config()
        
        assert config.download.retry_delay > 0


class TestPlatformConstants:
    """Tests for platform constants."""
    
    def test_platforms_defined(self):
        """Test platform constants are defined."""
        from hf_suite_v2.core.constants import PLATFORMS
        
        assert "huggingface" in PLATFORMS
        assert "modelscope" in PLATFORMS
    
    def test_platform_has_required_fields(self):
        """Test each platform has required fields."""
        from hf_suite_v2.core.constants import PLATFORMS
        
        for name, platform in PLATFORMS.items():
            assert "default_endpoint" in platform
            assert "token_url" in platform
    
    def test_huggingface_endpoint(self):
        """Test HuggingFace endpoint is valid."""
        from hf_suite_v2.core.constants import PLATFORMS
        
        hf = PLATFORMS["huggingface"]
        assert "huggingface" in hf["default_endpoint"].lower()
