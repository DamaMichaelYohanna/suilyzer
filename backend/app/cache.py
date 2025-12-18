"""
Simple in-memory cache for transaction analysis results.
"""
import time
from typing import Optional, Any, Dict
from datetime import datetime


class Cache:
    """In-memory cache with TTL support."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if exists and not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        current_time = time.time()
        
        # Check if entry has expired
        if current_time - entry["timestamp"] > self._ttl_seconds:
            del self._cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of items in cache."""
        return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry["timestamp"] > self._ttl_seconds
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)


# Global cache instance
transaction_cache = Cache(ttl_seconds=3600)
