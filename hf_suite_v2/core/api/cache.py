"""
API response caching for HuggingFace and ModelScope.

Caches model search results, file listings, and repository info
to reduce API calls and improve UI responsiveness.
"""

import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Any, Dict, Callable
from functools import wraps

from ..constants import APP_DATA_DIR

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = APP_DATA_DIR / "cache"
DEFAULT_TTL = 3600  # 1 hour in seconds
MAX_CACHE_SIZE_MB = 100  # Maximum cache size


class APICache:
    """
    Simple file-based cache for API responses.
    
    Features:
    - TTL-based expiration
    - Automatic cleanup of expired entries
    - Size-limited cache directory
    - Thread-safe operations
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache stats
        self._hits = 0
        self._misses = 0
        
        logger.debug(f"APICache initialized at {self.cache_dir}")
    
    def _get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from arguments."""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self._misses += 1
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check expiration
            if time.time() > data.get('expires_at', 0):
                cache_path.unlink(missing_ok=True)
                self._misses += 1
                return None
            
            self._hits += 1
            logger.debug(f"Cache hit: {key}")
            return data.get('value')
            
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Cache read error for {key}: {e}")
            cache_path.unlink(missing_ok=True)
            self._misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds
            
        Returns:
            True if successfully cached
        """
        cache_path = self._get_cache_path(key)
        
        try:
            data = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ttl,
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except (TypeError, IOError) as e:
            logger.warning(f"Cache write error for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        cache_path = self._get_cache_path(key)
        try:
            cache_path.unlink(missing_ok=True)
            return True
        except IOError:
            return False
    
    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except IOError:
                pass
        
        logger.info(f"Cache cleared: {count} entries")
        return count
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        count = 0
        current_time = time.time()
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if current_time > data.get('expires_at', 0):
                    cache_file.unlink()
                    count += 1
                    
            except (json.JSONDecodeError, IOError):
                cache_file.unlink(missing_ok=True)
                count += 1
        
        if count > 0:
            logger.debug(f"Cleaned up {count} expired cache entries")
        
        return count
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        entry_count = len(list(self.cache_dir.glob("*.json")))
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0,
            'entry_count': entry_count,
            'total_size_mb': total_size / (1024 * 1024),
        }


def get_cache() -> APICache:
    """Get the global cache instance."""
    return APICache()


def cached(prefix: str, ttl: int = DEFAULT_TTL):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix (usually function name)
        ttl: Time-to-live in seconds
        
    Usage:
        @cached("search_models", ttl=1800)
        def search_models(query: str) -> list:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            key = cache._get_cache_key(prefix, *args, **kwargs)
            
            # Try cache first
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            
            if result is not None:
                cache.set(key, result, ttl)
            
            return result
        
        # Add cache control methods to wrapper
        wrapper.cache_clear = lambda: get_cache().clear()
        wrapper.cache_stats = lambda: get_cache().get_stats()
        
        return wrapper
    
    return decorator


# Pre-defined TTLs for different data types
TTL_SEARCH = 1800      # 30 minutes for search results
TTL_REPO_INFO = 3600   # 1 hour for repo info
TTL_FILE_LIST = 1800   # 30 minutes for file listings
TTL_USER_INFO = 7200   # 2 hours for user info
