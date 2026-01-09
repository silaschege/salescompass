"""
Inference Caching Service.
Uses Redis (open-source in-memory store) to cache ML predictions for high performance.
"""

import json
import logging
import hashlib
from typing import Any, Optional, Dict
from datetime import timedelta

# Mock Redis interface for standalone compatibility
class RedisPlaceholder:
    def __init__(self):
        self.data = {}
    def get(self, key): return self.data.get(key)
    def setex(self, key, time, value): self.data[key] = value

try:
    import redis
    _client = redis.Redis(host='localhost', port=6379, db=0)
except ImportError:
    logging.warning("Redis library not found. Falling back to in-memory cache.")
    _client = RedisPlaceholder()

class InferenceCache:
    """
    Caching layer for ML predictions.
    """
    
    def __init__(self, prefix: str = "ml_cache"):
        self.prefix = prefix
        self.logger = logging.getLogger("infrastructure.cache")

    def _generate_key(self, model_id: str, input_data: Dict[str, Any]) -> str:
        # Create a stable hash of the input data
        data_str = json.dumps(input_data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{self.prefix}:{model_id}:{data_hash}"

    def get_prediction(self, model_id: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieves a cached prediction if it exists.
        """
        key = self._generate_key(model_id, input_data)
        cached = _client.get(key)
        
        if cached:
            self.logger.info(f"Cache HIT for {model_id}")
            return json.loads(cached)
            
        self.logger.info(f"Cache MISS for {model_id}")
        return None

    def set_prediction(self, model_id: str, input_data: Dict[str, Any], prediction: Dict[str, Any], ttl_seconds: int = 3600):
        """
        Caches a prediction with a Time-To-Live (TTL).
        """
        key = self._generate_key(model_id, input_data)
        _client.setex(key, ttl_seconds, json.dumps(prediction))
        self.logger.info(f"Cached prediction for {model_id} (TTL: {ttl_seconds}s)")
