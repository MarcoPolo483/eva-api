# ============================================================================
# EVA API - Session Management Router
# ============================================================================
# Purpose: Manage user sessions with 25-user capacity limit for demo
# Author: GitHub Copilot + Marco Presta
# Date: 2025-12-08
# ============================================================================

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

# ============================================================================
# Session Configuration
# ============================================================================

MAX_USERS = 25
SESSION_TIMEOUT = timedelta(minutes=30)  # 30 minutes idle timeout

# In-memory session store (use Redis for production)
# Format: { session_id: { connected_at, last_heartbeat, client_info } }
active_sessions = {}

# ============================================================================
# Request/Response Models
# ============================================================================

class ConnectRequest(BaseModel):
    """Client info sent when connecting"""
    browser: Optional[str] = None
    timestamp: Optional[str] = None
    user_agent: Optional[str] = None

class SessionResponse(BaseModel):
    """Standard session response"""
    session_id: str
    active_users: int
    max_users: int
    expires_in_seconds: int

class SessionStatusResponse(BaseModel):
    """Public status response"""
    active_users: int
    max_users: int
    available_slots: int
    at_capacity: bool

# ============================================================================
# Helper Functions
# ============================================================================

def cleanup_expired_sessions():
    """Remove sessions with no heartbeat in last 30 minutes"""
    now = datetime.utcnow()
    expired = [
        sid for sid, data in active_sessions.items()
        if now - data["last_heartbeat"] > SESSION_TIMEOUT
    ]
    
    if expired:
        for sid in expired:
            logger.info(f"🧹 Cleaning up expired session: {sid}")
            del active_sessions[sid]
        logger.info(f"✅ Cleaned up {len(expired)} expired sessions")
    
    return len(expired)

def verify_demo_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Verify demo API key for session management.
    For production, use proper JWT authentication.
    """
    if x_api_key != "demo-api-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# ============================================================================
# Session Endpoints
# ============================================================================

@router.post("/connect", response_model=SessionResponse)
async def connect_session(
    request: ConnectRequest,
    user_agent: Optional[str] = Header(None),
    api_key: str = Depends(verify_demo_api_key)
):
    """
    Connect a new user session.
    
    Returns 503 if at capacity (25 users).
    Returns 201 with session_id if successful.
    """
    
    # Clean up expired sessions first
    cleanup_expired_sessions()
    
    # Check capacity
    if len(active_sessions) >= MAX_USERS:
        logger.warning(f"🚫 Connection rejected: at capacity ({len(active_sessions)}/{MAX_USERS})")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Demo at capacity",
                "message": f"Currently {len(active_sessions)}/{MAX_USERS} users connected. Please try again later.",
                "active_users": len(active_sessions),
                "max_users": MAX_USERS,
                "retry_after_seconds": 900  # Suggest retry in 15 min
            }
        )
    
    # Create new session
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    active_sessions[session_id] = {
        "connected_at": now,
        "last_heartbeat": now,
        "client_info": {
            "browser": request.browser,
            "user_agent": user_agent or request.user_agent,
            "timestamp": request.timestamp
        }
    }
    
    logger.info(f"✅ New session connected: {session_id} ({len(active_sessions)}/{MAX_USERS} users)")
    
    return SessionResponse(
        session_id=session_id,
        active_users=len(active_sessions),
        max_users=MAX_USERS,
        expires_in_seconds=int(SESSION_TIMEOUT.total_seconds())
    )

@router.post("/{session_id}/heartbeat", response_model=SessionResponse)
async def session_heartbeat(
    session_id: str,
    api_key: str = Depends(verify_demo_api_key)
):
    """
    Keep session alive with heartbeat.
    
    Should be called every 30 seconds from client.
    """
    
    # Clean up expired sessions (not this one)
    cleanup_expired_sessions()
    
    # Check if session exists
    if session_id not in active_sessions:
        logger.warning(f"❌ Heartbeat failed: session not found {session_id}")
        raise HTTPException(
            status_code=404,
            detail="Session expired or not found. Please reconnect."
        )
    
    # Update last heartbeat
    active_sessions[session_id]["last_heartbeat"] = datetime.utcnow()
    
    logger.debug(f"💓 Heartbeat: {session_id} ({len(active_sessions)}/{MAX_USERS} users)")
    
    return SessionResponse(
        session_id=session_id,
        active_users=len(active_sessions),
        max_users=MAX_USERS,
        expires_in_seconds=int(SESSION_TIMEOUT.total_seconds())
    )

@router.post("/{session_id}/disconnect")
async def disconnect_session(
    session_id: str,
    api_key: str = Depends(verify_demo_api_key)
):
    """
    Disconnect user session (called on page close).
    """
    
    if session_id in active_sessions:
        del active_sessions[session_id]
        logger.info(f"👋 Session disconnected: {session_id} ({len(active_sessions)}/{MAX_USERS} users)")
    else:
        logger.warning(f"⚠️ Disconnect attempted for unknown session: {session_id}")
    
    return {
        "message": "Session disconnected",
        "active_users": len(active_sessions),
        "max_users": MAX_USERS
    }

@router.get("/status", response_model=SessionStatusResponse)
async def get_session_status():
    """
    Public endpoint to check capacity.
    
    No authentication required (useful for landing page).
    """
    
    # Clean up expired sessions
    cleanup_expired_sessions()
    
    return SessionStatusResponse(
        active_users=len(active_sessions),
        max_users=MAX_USERS,
        available_slots=MAX_USERS - len(active_sessions),
        at_capacity=len(active_sessions) >= MAX_USERS
    )

@router.get("/admin/list")
async def list_active_sessions(api_key: str = Depends(verify_demo_api_key)):
    """
    Admin endpoint: List all active sessions.
    
    Useful for debugging and monitoring.
    """
    
    cleanup_expired_sessions()
    
    sessions_list = []
    for sid, data in active_sessions.items():
        sessions_list.append({
            "session_id": sid,
            "connected_at": data["connected_at"].isoformat(),
            "last_heartbeat": data["last_heartbeat"].isoformat(),
            "age_seconds": (datetime.utcnow() - data["connected_at"]).total_seconds(),
            "idle_seconds": (datetime.utcnow() - data["last_heartbeat"]).total_seconds(),
            "client_info": data["client_info"]
        })
    
    return {
        "active_sessions": len(sessions_list),
        "max_users": MAX_USERS,
        "sessions": sessions_list
    }
