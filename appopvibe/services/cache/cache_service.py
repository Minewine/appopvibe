"""
Cache service for storing and retrieving cached data.
Uses Flask-Caching for managing cache operations.
"""
import functools
import hashlib
import json

try:
    from flask_caching import Cache
    CACHE_AVAILABLE = True
except ImportError:
    # Create a dummy cache that doesn't cache anything
    CACHE_AVAILABLE = False
    
    class DummyCache:
        def __init__(self, *args, **kwargs):
            pass
            
        def init_app(self, app):
            print("WARNING: Flask-Caching not installed. Running without cache functionality.")
            
        def memoize(self, timeout=None, *args, **kwargs):
            def decorator(f):
                @functools.wraps(f)
                def wrapper(*args, **kwargs):
                    return f(*args, **kwargs)
                return wrapper
            return decorator
            
        def get(self, key):
            return None
            
        def set(self, key, value, timeout=None):
            pass
    
    Cache = DummyCache

# Initialize cache instance
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',  # Use simple memory cache by default
    'CACHE_DEFAULT_TIMEOUT': 3600  # Default timeout of 1 hour
})

class CacheService:
    """Service for caching expensive operations."""
    
    def __init__(self, app=None):
        """Initialize with Flask app if provided."""
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        cache.init_app(app)
    
    def generate_cache_key(self, *args, **kwargs):
        """Generate a cache key from arguments."""
        key_parts = []
        
        # Add positional args
        for arg in args:
            key_parts.append(str(arg))
        
        # Add keyword args (sorted by key for consistency)
        for k in sorted(kwargs.keys()):
            key_parts.append(f"{k}:{kwargs[k]}")
        
        # Join and hash
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def memoize(self, timeout=3600):
        """Decorator to cache function results."""
        return cache.memoize(timeout=timeout)
    
    def cache_value(self, key, value, timeout=3600):
        """Manually cache a value."""
        return cache.set(key, value, timeout=timeout)
    
    def get_cached_value(self, key):
        """Retrieve a cached value."""
        return cache.get(key)
