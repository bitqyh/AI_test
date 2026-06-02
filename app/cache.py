import json
import hashlib
import logging
from typing import Optional
from datetime import timedelta

import redis.asyncio as aioredis

from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, CACHE_TTL_DAYS
from app.models import AnalysisResult

logger = logging.getLogger(__name__)


class MemoryCache:
    def __init__(self, ttl_days: int):
        self._store: dict[str, tuple[str, float]] = {}
        self._ttl = timedelta(days=ttl_days)

    async def get(self, key: str) -> Optional[str]:
        import time

        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.time() > expiry:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: str) -> None:
        import time

        expiry = time.time() + self._ttl.total_seconds()
        self._store[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class CacheManager:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._memory = MemoryCache(ttl_days=CACHE_TTL_DAYS)
        self._redis_available = False

    async def _ensure_redis(self):
        if self._redis is not None:
            return
        try:
            self._redis = aioredis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD or None,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            await self._redis.ping()
            self._redis_available = True
            logger.info("Redis 连接成功")
        except Exception:
            self._redis_available = False
            self._redis = None
            logger.warning("Redis 不可用，使用内存缓存作为降级方案")

    @staticmethod
    def build_cache_key(resume_md5: str, jd_md5: str) -> str:
        return f"resume_analysis:{resume_md5}:{jd_md5}"

    @staticmethod
    def compute_md5(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    async def get(self, resume_md5: str, jd_md5: str) -> Optional[AnalysisResult]:
        await self._ensure_redis()
        key = self.build_cache_key(resume_md5, jd_md5)
        try:
            if self._redis_available:
                value = await self._redis.get(key)
                if value:
                    data = json.loads(value)
                    return AnalysisResult(**data)
            value = await self._memory.get(key)
            if value:
                return AnalysisResult(**json.loads(value))
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
        return None

    async def set(
        self, resume_md5: str, jd_md5: str, result: AnalysisResult
    ) -> None:
        await self._ensure_redis()
        key = self.build_cache_key(resume_md5, jd_md5)
        value = json.dumps(result.model_dump(), ensure_ascii=False)
        try:
            if self._redis_available:
                ttl = timedelta(days=CACHE_TTL_DAYS)
                await self._redis.setex(key, ttl, value)
            await self._memory.set(key, value)
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")
            await self._memory.set(key, value)

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None


cache_manager = CacheManager()
