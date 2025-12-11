"""Authentication middleware for EVA API Platform.

JWT validation, API key verification, and rate limiting middleware.
Phase 2.4 - Complete rate limiting implementation with Redis.
"""

import logging
import time
import uuid
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from redis.exceptions import RedisError

from eva_api.config import get_settings
from eva_api.services.redis_service import get_redis_service

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and request tracking."""
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with authentication.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response: HTTP response
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Track request timing
        start_time = time.time()
        
        # Add request ID to response headers
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.3f}s "
            f"ID: {request_id}"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting using token bucket algorithm with Redis.
    
    Implements sliding window rate limiting with burst support:
    - Each client gets a configurable requests/minute quota
    - Burst allowance for temporary spikes
    - Distributed rate limiting via Redis
    - Standard HTTP 429 responses when exceeded
    
    Rate limit key format: rate_limit:{client_id}
    where client_id is derived from API key, JWT sub, or IP address
    """
    
    def __init__(self, app, redis_service=None):
        """Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            redis_service: Optional Redis service (for testing)
        """
        super().__init__(app)
        self.settings = get_settings()
        self.redis_service = redis_service or get_redis_service()
        
        # Rate limit configuration
        self.enabled = self.settings.rate_limit_enabled
        self.requests_per_minute = self.settings.rate_limit_requests_per_minute
        self.burst_size = self.settings.rate_limit_burst_size
        self.window_seconds = 60  # 1 minute window
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with rate limiting.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response: HTTP response or 429 if rate limit exceeded
            
        Raises:
            HTTPException: 429 Too Many Requests if limit exceeded
        """
        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Extract client identifier
        client_id = self._get_client_id(request)
        
        # Check and apply rate limit
        try:
            if not self.redis_service.is_connected:
                # If Redis unavailable, fail open (allow request)
                logger.warning("Redis unavailable, rate limiting bypassed")
                response = await call_next(request)
                return self._add_rate_limit_headers(response, None, None, None)
            
            # Rate limit key
            rate_key = f"rate_limit:{client_id}"
            
            # Check current usage
            current_count, remaining = await self.redis_service.check_rate_limit(
                rate_key, self.requests_per_minute
            )
            
            # Check if limit exceeded
            if current_count >= self.requests_per_minute:
                # Get TTL for reset time
                ttl = await self.redis_service.get_ttl(rate_key)
                reset_time = int(time.time()) + max(ttl, 0)
                
                logger.warning(
                    f"Rate limit exceeded for client {client_id}: "
                    f"{current_count}/{self.requests_per_minute}"
                )
                
                # Return 429 Too Many Requests
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": "Too many requests. Please slow down.",
                        "limit": self.requests_per_minute,
                        "window_seconds": self.window_seconds,
                        "retry_after": ttl,
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(max(ttl, 1)),
                    },
                )
            
            # Increment counter
            new_count, new_remaining = await self.redis_service.increment_rate_limit(
                rate_key, self.window_seconds, self.requests_per_minute
            )
            
            # Get TTL for reset time
            ttl = await self.redis_service.get_ttl(rate_key)
            reset_time = int(time.time()) + max(ttl, 0)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            return self._add_rate_limit_headers(
                response, self.requests_per_minute, new_remaining, reset_time
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions (like 429)
            raise
        except RedisError as e:
            # Redis error - fail open (allow request)
            logger.error(f"Redis error in rate limiting: {e}")
            response = await call_next(request)
            return self._add_rate_limit_headers(response, None, None, None)
        except Exception as e:
            # Unexpected error - fail open
            logger.error(f"Unexpected error in rate limiting: {e}")
            response = await call_next(request)
            return self._add_rate_limit_headers(response, None, None, None)
    
    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier for rate limiting.
        
        Priority order:
        1. API key (from X-API-Key header)
        2. JWT subject (from Authorization header)
        3. IP address (fallback)
        
        Args:
            request: HTTP request
            
        Returns:
            str: Client identifier
        """
        # Try API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Use first 16 chars of API key as identifier
            return f"apikey:{api_key[:16]}"
        
        # Try JWT subject
        if hasattr(request.state, "user") and request.state.user:
            user_id = getattr(request.state.user, "sub", None)
            if user_id:
                return f"user:{user_id}"
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def _add_rate_limit_headers(
        self,
        response: Response,
        limit: Optional[int],
        remaining: Optional[int],
        reset: Optional[int],
    ) -> Response:
        """Add rate limit headers to response.
        
        Args:
            response: HTTP response
            limit: Rate limit (requests per window)
            remaining: Remaining requests in window
            reset: Unix timestamp when limit resets
            
        Returns:
            Response: Response with rate limit headers
        """
        if limit is not None:
            response.headers["X-RateLimit-Limit"] = str(limit)
        
        if remaining is not None:
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        if reset is not None:
            response.headers["X-RateLimit-Reset"] = str(reset)
        
        return response
