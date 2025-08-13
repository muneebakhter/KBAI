"""
Unified authentication dependencies supporting both JWT tokens and API keys.
"""
from __future__ import annotations

import os
import secrets
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth import get_current_session, decode_token

# Initialize API token with precedence: env > auto-generated
KBAI_API_TOKEN = os.environ.get("KBAI_API_TOKEN")
if not KBAI_API_TOKEN:
    KBAI_API_TOKEN = secrets.token_hex(32)
    print(f"⚠️  WARNING: KBAI_API_TOKEN auto-generated. Set environment variable for production.")
    print(f"   Generated token: {KBAI_API_TOKEN}")

security = HTTPBearer(auto_error=False)


async def get_current_auth(
    request: Request, 
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Unified authentication dependency that accepts either:
    1. Valid Bearer JWT token (existing behavior)
    2. Valid X-API-Key header matching KBAI_API_TOKEN
    
    Returns session info with scopes for JWT, or API key info for API key auth.
    """
    # Check for X-API-Key header first
    api_key = request.headers.get("x-api-key")
    if api_key:
        if api_key == KBAI_API_TOKEN:
            # API key authentication successful
            # Store API key auth info on request state for tracing
            request.state.session_id = "api_key_auth"
            request.state.session_scopes = ["api_key", "read:basic", "read:traces", "read:metrics", "write:projects"]
            request.state.auth_method = "api_key"
            return {
                "session_id": "api_key_auth",
                "scopes": request.state.session_scopes,
                "auth_method": "api_key"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid API key"
            )
    
    # Fall back to JWT authentication
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing authentication - provide either Bearer token or X-API-Key header"
        )
    
    # Use existing JWT authentication
    session = await get_current_session(request, credentials)
    session["auth_method"] = "jwt"
    request.state.auth_method = "jwt"
    return session


def require_scopes_unified(required: list[str]):
    """
    Scope checker that works with both JWT and API key authentication.
    API key auth has full permissions by default.
    """
    async def _dep(request: Request):
        auth_method = getattr(request.state, "auth_method", None)
        scopes = getattr(request.state, "session_scopes", [])
        
        if not scopes:
            raise HTTPException(status_code=401, detail="unauthorized")
        
        # API key auth has full access
        if auth_method == "api_key":
            return True
            
        # JWT auth requires scope checking
        missing = [s for s in required if s not in scopes]
        if missing:
            raise HTTPException(
                status_code=403, 
                detail=f"missing scopes: {','.join(missing)}"
            )
        return True
    return _dep