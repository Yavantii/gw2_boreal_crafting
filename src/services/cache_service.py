"""
Cache-Service für die Zwischenspeicherung von API-Antworten und Berechnungen
"""

import json
from datetime import datetime
from functools import wraps
from config.settings import CACHE_DURATION

class CacheService:
    def __init__(self):
        self._cache = {}
        
    def _get_cache_key(self, prefix, *args, **kwargs):
        """Generiert einen eindeutigen Cache-Key"""
        key_parts = [prefix]
        if args:
            key_parts.extend(str(arg) for arg in args)
        if kwargs:
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return "_".join(key_parts)
        
    def get(self, key):
        """
        Holt einen Wert aus dem Cache
        
        Args:
            key: Cache-Schlüssel
            
        Returns:
            Der gecachte Wert oder None wenn nicht gefunden/abgelaufen
        """
        if key not in self._cache:
            return None
            
        value, timestamp = self._cache[key]
        if (datetime.now() - timestamp) > CACHE_DURATION:
            del self._cache[key]
            return None
            
        return value
        
    def set(self, key, value):
        """
        Speichert einen Wert im Cache
        
        Args:
            key: Cache-Schlüssel
            value: Zu cachender Wert
        """
        self._cache[key] = (value, datetime.now())
        
    def delete(self, key):
        """Löscht einen Wert aus dem Cache"""
        if key in self._cache:
            del self._cache[key]
            
    def clear(self):
        """Leert den gesamten Cache"""
        self._cache.clear()
        
    def cleanup(self):
        """Entfernt abgelaufene Cache-Einträge"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if (now - timestamp) > CACHE_DURATION
        ]
        for key in expired_keys:
            del self._cache[key]

def cache_result(prefix):
    """
    Decorator für das Caching von Funktionsaufrufen
    
    Args:
        prefix: Präfix für den Cache-Key
        
    Returns:
        Decorator-Funktion
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            cache_service = getattr(self, 'cache_service', None)
            if not cache_service:
                return func(self, *args, **kwargs)
                
            cache_key = cache_service._get_cache_key(prefix, *args, **kwargs)
            result = cache_service.get(cache_key)
            
            if result is None:
                result = func(self, *args, **kwargs)
                if result is not None:
                    cache_service.set(cache_key, result)
                    
            return result
        return wrapper
    return decorator 