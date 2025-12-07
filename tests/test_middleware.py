"""Tests for authentication middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from eva_api.middleware.auth import AuthenticationMiddleware, RateLimitMiddleware


def test_authentication_middleware_adds_request_id() -> None:
    """Test that authentication middleware adds request ID."""
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    assert "x-request-id" in response.headers
    assert "x-process-time" in response.headers


def test_authentication_middleware_request_id_unique() -> None:
    """Test that each request gets unique ID."""
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    response1 = client.get("/test")
    response2 = client.get("/test")
    
    assert response1.headers["x-request-id"] != response2.headers["x-request-id"]


def test_authentication_middleware_measures_time() -> None:
    """Test that middleware measures processing time."""
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    process_time = float(response.headers["x-process-time"])
    assert process_time >= 0


def test_rate_limit_middleware_adds_headers() -> None:
    """Test that rate limit middleware adds headers."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers
    assert "x-ratelimit-reset" in response.headers


def test_rate_limit_middleware_placeholder_values() -> None:
    """Test rate limit middleware placeholder values."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    # Verify placeholder values
    assert response.headers["x-ratelimit-limit"] == "1000"
    assert response.headers["x-ratelimit-remaining"] == "999"
    assert int(response.headers["x-ratelimit-reset"]) > 0


def test_middleware_chain_order() -> None:
    """Test that both middlewares work together."""
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    # Should have headers from both middlewares
    assert "x-request-id" in response.headers
    assert "x-process-time" in response.headers
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers
