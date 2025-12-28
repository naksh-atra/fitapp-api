# src/validation/validation_cache.py
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

class ValidationCache:
    def __init__(self, cache_dir: str = "data/validation_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_days = 30  # Cache research validations for 30 days
    
    def get_cached_validation(self, original: str, replacement: str, reason: str, goal: str):
        """Check if we've validated this swap recently."""
        cache_key = self._generate_key(original, replacement, reason, goal)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            with open(cache_file) as f:
                cached = json.load(f)
            
            # Check if cache is still fresh
            cached_date = datetime.fromisoformat(cached['timestamp'])
            if datetime.now() - cached_date < timedelta(days=self.ttl_days):
                return cached
        
        return None
    
    def save_validation(self, original: str, replacement: str, reason: str, goal: str, result: Dict):
        """Save validation result to cache."""
        cache_key = self._generate_key(original, replacement, reason, goal)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        result['timestamp'] = datetime.now().isoformat()
        
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    def _generate_key(self, original: str, replacement: str, reason: str, goal: str) -> str:
        """Generate unique cache key for this validation."""
        components = f"{original}|{replacement}|{reason}|{goal}".lower()
        return hashlib.md5(components.encode()).hexdigest()
