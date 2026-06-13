"""
Authentication Routes for TRAMOS Dashboard
Full registration + login system with email OTP verification, Google SSO, and bcrypt hashing.
"""
import logging
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status, Depends
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
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = settings.TOKEN_EXPIRE_MINUTES

# Legacy admin hanya boleh aktif jika password diisi eksplisit dari .env.
LEGACY_ADMIN_USERNAME = settings.DASHBOARD_USERNAME
LEGACY_ADMIN_PASSWORD = settings.DASHBOARD_PASSWORD
LEGACY_ADMIN_ENABLED = settings.DASHBOARD_ENABLE_LEGACY_ADMIN and bool(LEGACY_ADMIN_PASSWORD)


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


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Ambil JWT dari header Authorization: Bearer <token>."""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def send_verification_email_or_fail(email: str, otp: str, name: str) -> None:
    """Kirim OTP dan hentikan respons sukses jika layanan email gagal."""
    if send_otp_email(email, otp, name):
        return

    logger.error("OTP delivery failed for %s", email)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Kode verifikasi belum dapat dikirim. "
            "Silakan coba Kirim Ulang beberapa saat lagi."
        ),
    )


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

        send_verification_email_or_fail(email, otp, request.full_name.strip())

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
    send_verification_email_or_fail(email, otp, request.full_name.strip())

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

    send_verification_email_or_fail(email, otp, user.full_name)

    return {"message": "Kode OTP baru telah dikirim ke email kamu."}


# ============================================================================
# LOGIN
# ============================================================================

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email/phone + password"""
    identifier = request.username.strip().lower()

    # Legacy admin hanya untuk development/demo, dan harus diaktifkan dengan password eksplisit.
    if LEGACY_ADMIN_ENABLED and identifier == LEGACY_ADMIN_USERNAME and request.password == LEGACY_ADMIN_PASSWORD:
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
    """
    Google SSO — two modes:
    - is_signup=True  → register new account via Google (must not already exist, sends OTP for verification)
    - is_signup=False → login with existing verified Google-linked account
    """
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

        user = db.query(DashboardUser).filter(DashboardUser.email == email).first()

        if request.is_signup:
            # ── SIGN UP via Google ──
            if user and user.is_verified:
                raise HTTPException(status_code=400, detail="Email sudah terdaftar. Silakan login.")

            if user and not user.is_verified:
                # Update existing unverified account with Google info
                user.full_name = name
                user.google_id = google_id
                user.auth_provider = "google"
                otp = generate_otp()
                user.otp_code = otp
                user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
                db.commit()
                send_verification_email_or_fail(email, otp, name)
                return {
                    "needs_verification": True,
                    "message": "Kode OTP telah dikirim ke email kamu untuk verifikasi.",
                    "email": email,
                }

            # Create new user — send OTP for verification
            otp = generate_otp()
            new_user = DashboardUser(
                email=email,
                full_name=name,
                google_id=google_id,
                auth_provider="google",
                is_verified=False,
                otp_code=otp,
                otp_expires_at=datetime.utcnow() + timedelta(minutes=10),
                role="user",
            )
            db.add(new_user)
            db.commit()

            send_verification_email_or_fail(email, otp, name)
            logger.info(f"New Google sign-up (pending OTP): {email}")

            return {
                "needs_verification": True,
                "message": "Akun berhasil dibuat! Cek email untuk kode verifikasi.",
                "email": email,
            }
        else:
            # ── SIGN IN via Google ──
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Akun belum terdaftar. Silakan daftar terlebih dahulu."
                )

            if not user.is_verified:
                raise HTTPException(
                    status_code=403,
                    detail="Akun belum diverifikasi. Cek email untuk kode OTP."
                )

            # Login successful
            user.last_login_at = datetime.utcnow()
            if not user.google_id:
                user.google_id = google_id
            db.commit()

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
async def get_current_user(
    token: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
):
    """Get current user info from JWT"""
    token = extract_bearer_token(authorization) or token
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


@router.delete("/me")
async def delete_current_user(
    token: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """Hapus akun dashboard milik user yang sedang login.

    Endpoint ini hanya menghapus akun lokal TRAMOS Dashboard. Akun Google asli
    tetap aman karena berada di luar sistem TRAMOS.
    """
    token = extract_bearer_token(authorization) or token
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token tidak valid atau kedaluwarsa")

    email = (payload.get("email") or payload.get("sub") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Identitas akun tidak lengkap.")

    user = db.query(DashboardUser).filter(DashboardUser.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan atau sudah dihapus.")

    deleted_email = user.email
    db.delete(user)
    db.commit()

    logger.info("Dashboard account deleted: %s", deleted_email)
    return {
        "message": "Akun dashboard berhasil dihapus.",
        "email": deleted_email,
    }


# ============================================================================
# VERIFY TOKEN
# ============================================================================

@router.post("/verify")
async def verify(
    token: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
):
    """Verify token endpoint"""
    token = extract_bearer_token(authorization) or token
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
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
