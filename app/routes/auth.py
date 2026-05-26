"""
Authentication Routes for TRAMOS Dashboard
Full registration + login system with email OTP verification, Google SSO, and bcrypt hashing.
"""
import logging
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import jwt
import os

from app.database_models import DatabaseManager, DashboardUser
from app.config import settings
from app.utils.otp_email import generate_otp, send_otp_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# JWT Config
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tramos_dashboard_secret_key_change_me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Legacy admin (fallback so you're never locked out)
LEGACY_ADMIN_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
LEGACY_ADMIN_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")


# ============================================================================
# DATABASE DEPENDENCY
# ============================================================================

def get_db():
    """Get database session"""
    from main import db_manager
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not available")
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    phone: Optional[str] = None

class VerifyOTPRequest(BaseModel):
    email: str
    otp_code: str

class ResendOTPRequest(BaseModel):
    email: str

class LoginRequest(BaseModel):
    username: str  # email, phone, or username
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: str
    is_signup: bool = False  # True if from sign-up page

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict

class UserInfo(BaseModel):
    username: str
    name: str
    email: str
    role: str


# ============================================================================
# HELPERS
# ============================================================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(subject: str, name: str = "", role: str = "user", email: str = ""):
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": subject,
        "name": name,
        "role": role,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None:
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ============================================================================
# REGISTER
# ============================================================================

@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new dashboard user account"""
    email = request.email.strip().lower()
    
    # Check if already exists
    existing = db.query(DashboardUser).filter(DashboardUser.email == email).first()
    if existing and existing.is_verified:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar. Silakan login.")
    
    if existing and not existing.is_verified:
        # Re-send OTP for unverified account
        otp = generate_otp()
        existing.otp_code = otp
        existing.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
        existing.full_name = request.full_name.strip()
        existing.password_hash = hash_password(request.password)
        if request.phone:
            existing.phone = request.phone.strip()
        db.commit()
        
        send_otp_email(email, otp, request.full_name.strip())
        
        return {"message": "Kode OTP telah dikirim ulang ke email kamu.", "email": email}
    
    # Create new user
    otp = generate_otp()
    new_user = DashboardUser(
        email=email,
        full_name=request.full_name.strip(),
        password_hash=hash_password(request.password),
        phone=request.phone.strip() if request.phone else None,
        auth_provider="email",
        is_verified=False,
        otp_code=otp,
        otp_expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(new_user)
    db.commit()
    
    # Send OTP email
    email_sent = send_otp_email(email, otp, request.full_name.strip())
    
    if not email_sent:
        logger.warning(f"OTP email failed for {email}, but account created")
    
    logger.info(f"New user registered: {email}")
    return {"message": "Akun berhasil dibuat! Cek email untuk kode verifikasi.", "email": email}


# ============================================================================
# VERIFY OTP
# ============================================================================

@router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP code to activate account"""
    email = request.email.strip().lower()
    
    user = db.query(DashboardUser).filter(DashboardUser.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan.")
    
    if user.is_verified:
        return {"message": "Akun sudah terverifikasi. Silakan login.", "verified": True}
    
    # Check OTP
    if not user.otp_code or user.otp_code != request.otp_code.strip():
        raise HTTPException(status_code=400, detail="Kode OTP salah.")
    
    if user.otp_expires_at and datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="Kode OTP sudah kedaluwarsa. Kirim ulang kode.")
    
    # Activate
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    
    logger.info(f"User verified: {email}")
    return {"message": "Akun berhasil diverifikasi! Silakan login.", "verified": True}


# ============================================================================
# RESEND OTP
# ============================================================================

@router.post("/resend-otp")
async def resend_otp(request: ResendOTPRequest, db: Session = Depends(get_db)):
    """Resend OTP verification code"""
    email = request.email.strip().lower()
    
    user = db.query(DashboardUser).filter(DashboardUser.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan.")
    
    if user.is_verified:
        return {"message": "Akun sudah terverifikasi."}
    
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    send_otp_email(email, otp, user.full_name)
    
    return {"message": "Kode OTP baru telah dikirim ke email kamu."}


# ============================================================================
# LOGIN
# ============================================================================

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email/phone + password"""
    identifier = request.username.strip().lower()
    
    # Legacy admin check (so you're never locked out)
    if identifier == LEGACY_ADMIN_USERNAME and request.password == LEGACY_ADMIN_PASSWORD:
        token = create_access_token(
            subject=LEGACY_ADMIN_USERNAME,
            name="Admin",
            role="admin",
            email=""
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": TOKEN_EXPIRE_MINUTES * 60,
            "user": {"name": "Admin", "email": "", "role": "admin"}
        }
    
    # Find user by email or phone
    user = db.query(DashboardUser).filter(
        (DashboardUser.email == identifier) | (DashboardUser.phone == identifier)
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Akun tidak ditemukan. Silakan buat akun terlebih dahulu.")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Akun belum diverifikasi. Cek email untuk kode OTP.")
    
    if not user.password_hash:
        raise HTTPException(status_code=401, detail="Akun ini terdaftar via Google. Gunakan tombol Google untuk login.")
    
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Password salah.")
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    token = create_access_token(
        subject=user.email,
        name=user.full_name,
        role=user.role,
        email=user.email
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRE_MINUTES * 60,
        "user": {"name": user.full_name, "email": user.email, "role": user.role}
    }


# ============================================================================
# GOOGLE OAUTH
# ============================================================================

@router.post("/google")
async def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Google SSO — auto-registers new users, logs in existing ones"""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        
        idinfo = google_id_token.verify_oauth2_token(
            request.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        email = idinfo.get("email", "").lower()
        name = idinfo.get("name", email)
        google_id = idinfo.get("sub", "")
        
        if not email:
            raise HTTPException(status_code=400, detail="Tidak dapat mengambil email dari akun Google.")
        
        # Check if user exists
        user = db.query(DashboardUser).filter(DashboardUser.email == email).first()
        
        if user:
            # Existing user — log in
            user.last_login_at = datetime.utcnow()
            if not user.google_id:
                user.google_id = google_id
            db.commit()
        else:
            # New user — auto-register (Google users are auto-verified)
            user = DashboardUser(
                email=email,
                full_name=name,
                google_id=google_id,
                auth_provider="google",
                is_verified=True,  # Google accounts are pre-verified
                role="user",
            )
            db.add(user)
            db.commit()
            logger.info(f"New Google user auto-registered: {email}")
        
        token = create_access_token(
            subject=user.email,
            name=user.full_name,
            role=user.role,
            email=user.email
        )
        
        logger.info(f"Google login for: {email}")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": TOKEN_EXPIRE_MINUTES * 60,
            "user": {"name": user.full_name, "email": user.email, "role": user.role}
        }
        
    except ValueError as e:
        logger.warning(f"Invalid Google token: {e}")
        raise HTTPException(status_code=401, detail="Token Google tidak valid.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(status_code=500, detail=f"Google authentication gagal: {str(e)}")


# ============================================================================
# USER INFO
# ============================================================================

@router.get("/me")
async def get_current_user(token: Optional[str] = None):
    """Get current user info from JWT"""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token tidak valid atau kedaluwarsa")
    
    return {
        "username": payload.get("sub", ""),
        "name": payload.get("name", "User"),
        "email": payload.get("email", ""),
        "role": payload.get("role", "user"),
    }


# ============================================================================
# VERIFY TOKEN
# ============================================================================

@router.post("/verify")
async def verify(token: str):
    """Verify token endpoint"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"valid": True, "username": payload.get("sub")}


# ============================================================================
# LOGOUT
# ============================================================================

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Logged out successfully"}
