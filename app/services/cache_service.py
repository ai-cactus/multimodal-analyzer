"""
Redis Cache Service for LLM responses and embeddings
"""
import redis
import json
import hashlib
from typing import Optional, Any
from app.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class CacheService:
    """
    Redis-based caching for expensive operations
    """
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Operating without cache.")
            self.redis_client = None
    
    def _make_key(self, prefix: str, data: str) -> str:
        """Generate cache key from data hash"""
        hash_value = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_value}"
    
    async def get_llm_response(self, prompt: str, model: str) -> Optional[dict]:
        """Get cached LLM response"""
        if not self.redis_client:
            return None
        
        try:
            key = self._make_key(f"llm:{model}", prompt)
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache HIT for {model} LLM response")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def set_llm_response(
        self,
        prompt: str,
        model: str,
        response: dict,
        ttl: int = 86400  # 24 hours
    ):
        """Cache LLM response"""
        if not self.redis_client:
            return
        
        try:
            key = self._make_key(f"llm:{model}", prompt)
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(response)
            )
            logger.info(f"Cached {model} LLM response")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def get_embedding(self, text: str) -> Optional[list]:
        """Get cached embedding"""
        if not self.redis_client:
            return None
        
        try:
            key = self._make_key("embedding", text)
            cached = self.redis_client.get(key)
            if cached:
                logger.info("Cache HIT for embedding")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def set_embedding(
        self,
        text: str,
        embedding: list,
        ttl: int = 604800  # 7 days
    ):
        """Cache embedding"""
        if not self.redis_client:
            return
        
        try:
            key = self._make_key("embedding", text)
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(embedding)
            )
            logger.info("Cached embedding")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")


# Singleton
_cache_instance = None

def get_cache_service() -> CacheService:
    """Get CacheService instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
