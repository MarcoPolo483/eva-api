"""Redis service for caching and rate limiting.

This service provides connection pooling, retry logic, and health monitoring
for Redis operations used in rate limiting and caching.

Phase 2.4 - Redis Rate Limiting Infrastructure
"""

import asyncio
import logging
from typing import Optional
from functools import lru_cache

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from eva_api.config import get_settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis operations with connection pooling and resilience."""

    def __init__(self):
        """Initialize Redis service with lazy connection."""
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._settings = get_settings()
        self._is_connected = False

    async def connect(self) -> None:
        """Establish Redis connection pool.

        Raises:
            ConnectionError: If Redis connection fails after retries
        """
        if self._is_connected:
            logger.info("Redis already connected")
            return

        try:
            # Create connection pool
            pool_kwargs = {
                "host": self._settings.redis_host,
                "port": self._settings.redis_port,
                "password": self._settings.redis_password or None,
                "db": self._settings.redis_db,
                "decode_responses": True,
                "max_connections": self._settings.redis_max_connections,
                "socket_timeout": self._settings.redis_socket_timeout,
                "socket_connect_timeout": self._settings.redis_socket_connect_timeout,
                "health_check_interval": 30,  # Check connection health every 30s
                "retry_on_timeout": True,
            }
            
            # Only add SSL if enabled (avoid passing False which causes issues)
            if self._settings.redis_ssl:
                pool_kwargs["ssl"] = True
            
            self._pool = ConnectionPool(**pool_kwargs)

            # Create Redis client
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()
            self._is_connected = True

            logger.info(
                "Redis connected successfully",
                extra={
                    "host": self._settings.redis_host,
                    "port": self._settings.redis_port,
                    "db": self._settings.redis_db,
                },
            )

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection failed: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}") from e

    async def disconnect(self) -> None:
        """Close Redis connection pool gracefully."""
        if self._client:
            await self._client.aclose()
            self._client = None

        if self._pool:
            await self._pool.aclose()
            self._pool = None

        self._is_connected = False
        logger.info("Redis disconnected")

    async def health_check(self) -> dict:
        """Check Redis connectivity and performance.

        Returns:
            dict: Health check results with status and latency
        """
        if not self._is_connected or not self._client:
            return {
                "status": "unhealthy",
                "message": "Redis not connected",
                "connected": False,
            }

        try:
            # Measure ping latency
            import time

            start = time.time()
            await self._client.ping()
            latency_ms = (time.time() - start) * 1000

            # Get connection pool info
            pool_info = self._pool.get_connection("info") if self._pool else None

            return {
                "status": "healthy",
                "message": "Redis operational",
                "connected": True,
                "latency_ms": round(latency_ms, 2),
                "host": self._settings.redis_host,
                "port": self._settings.redis_port,
                "db": self._settings.redis_db,
            }

        except RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis error: {str(e)}",
                "connected": False,
            }

    # Rate Limiting Operations

    async def increment_rate_limit(
        self, key: str, window_seconds: int, max_requests: int
    ) -> tuple[int, int]:
        """Increment rate limit counter using sliding window.

        Args:
            key: Rate limit key (e.g., "rate_limit:user_123")
            window_seconds: Time window in seconds
            max_requests: Maximum requests allowed in window

        Returns:
            tuple: (current_count, remaining_requests)

        Raises:
            RedisError: If Redis operation fails
        """
        if not self._client:
            raise RedisError("Redis client not initialized")

        try:
            # Use INCR for atomic increment
            current = await self._client.incr(key)

            # Set expiration on first request
            if current == 1:
                await self._client.expire(key, window_seconds)

            remaining = max(0, max_requests - current)
            return current, remaining

        except RedisError as e:
            logger.error(f"Rate limit increment failed: {e}")
            raise

    async def check_rate_limit(self, key: str, max_requests: int) -> tuple[int, int]:
        """Check current rate limit status without incrementing.

        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed

        Returns:
            tuple: (current_count, remaining_requests)
        """
        if not self._client:
            raise RedisError("Redis client not initialized")

        try:
            current = await self._client.get(key)
            current_count = int(current) if current else 0
            remaining = max(0, max_requests - current_count)
            return current_count, remaining

        except RedisError as e:
            logger.error(f"Rate limit check failed: {e}")
            raise

    async def get_ttl(self, key: str) -> int:
        """Get time-to-live for a key in seconds.

        Args:
            key: Redis key

        Returns:
            int: TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        if not self._client:
            raise RedisError("Redis client not initialized")

        try:
            return await self._client.ttl(key)
        except RedisError as e:
            logger.error(f"TTL check failed: {e}")
            raise

    # Caching Operations (for Phase 3+)

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Optional[str]: Cached value or None
        """
        if not self._client:
            raise RedisError("Redis client not initialized")

        try:
            return await self._client.get(key)
        except RedisError as e:
            logger.error(f"Cache get failed: {e}")
            raise

    async def set(
        self, key: str, value: str, expire_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional expiration.

        Args:
            key: Cache key
            value: Value to cache
            expire_seconds: Expiration time in seconds (None = no expiry)

        Returns:
            bool: True if successful
        """
        if not self._client:
            raise RedisError("Redis client not initialized")

        try:
            if expire_seconds:
                return await self._client.setex(key, expire_seconds, value)
            else:
                return await self._client.set(key, value)
        except RedisError as e:
            logger.error(f"Cache set failed: {e}")
            raise

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key

        Returns:
            bool: True if key was deleted
        """
        if not self._client:
            raise RedisError("Redis client not initialized")

        try:
            result = await self._client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Cache delete failed: {e}")
            raise

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._is_connected


# Singleton instance
_redis_service: Optional[RedisService] = None


@lru_cache()
def get_redis_service() -> RedisService:
    """Get singleton Redis service instance.

    Returns:
        RedisService: Cached Redis service instance
    """
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service
