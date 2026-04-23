"""
Authentication Routes for Dashboard
Simple JWT-based authentication
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import jwt
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Simple hardcoded credentials (in production, use proper auth system)
VALID_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
VALID_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tramos_dashboard_secret_key_change_me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 480  # 8 hours


class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str
    expires_in: int


class UserInfo(BaseModel):
    """User info"""
    username: str
    name: str
    role: str


def create_access_token(username: str, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": username,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return username"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    # Simple validation
    if request.username != VALID_USERNAME or request.password != VALID_PASSWORD:
        logger.warning(f"Failed login attempt for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token
    access_token = create_access_token(request.username)
    
    logger.info(f"User {request.username} logged in successfully")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/verify")
async def verify(token: str):
    """Verify token endpoint"""
    username = verify_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {
        "valid": True,
        "username": username
    }


@router.get("/me", response_model=UserInfo)
async def get_current_user(token: Optional[str] = None):
    """Get current user info"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )
    
    username = verify_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {
        "username": username,
        "name": "Dashboard Admin",
        "role": "admin"
    }


@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token cleanup)"""
    return {"message": "Logged out successfully"}
