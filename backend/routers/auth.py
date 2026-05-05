"""
routers/auth.py – Authentication REST API endpoints.

POST /api/auth/signup        – Register + send OTP email
POST /api/auth/verify-otp   – Verify OTP & activate account
POST /api/auth/resend-otp   – Resend OTP
POST /api/auth/login        – Login → JWT
GET  /api/auth/me           – Get current user profile
"""
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from cache import get_user_cache, set_user_cache, invalidate_user_cache
from database import get_db
from email_service import generate_otp, get_otp_expiry, send_otp_email
import models
import schemas

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── POST /api/auth/signup ─────────────────────────────────────────────────────

@router.post("/signup", response_model=schemas.MessageResponse, status_code=201)
def signup(
    body: schemas.SignupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Check if email already registered
    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        if existing.is_verified:
            raise HTTPException(status_code=409, detail="Email already registered")
        # Unverified account – resend OTP
        _send_new_otp(existing.email, existing.name, db, background_tasks)
        return {"message": "Account exists but unverified. A new OTP has been sent."}

    # Create new user (unverified)
    user = models.User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        is_verified=False,
        role=models.UserRole.member,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send OTP in background
    _send_new_otp(user.email, user.name, db, background_tasks)

    return {"message": "Account created! Check your email for the OTP verification code."}


# ── POST /api/auth/verify-otp ─────────────────────────────────────────────────

@router.post("/verify-otp", response_model=schemas.TokenResponse)
def verify_otp(body: schemas.VerifyOtpRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Account already verified")

    # Find latest valid OTP
    otp_record = (
        db.query(models.OtpVerification)
        .filter(
            models.OtpVerification.email == body.email,
            models.OtpVerification.otp_code == body.otp_code,
            models.OtpVerification.is_used == False,
        )
        .order_by(models.OtpVerification.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Check expiry
    now = datetime.now(timezone.utc)
    expires = otp_record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now > expires:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

    # Mark OTP used & activate user
    otp_record.is_used = True
    user.is_verified = True
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": schemas.UserOut.model_validate(user),
    }


# ── POST /api/auth/resend-otp ─────────────────────────────────────────────────

@router.post("/resend-otp", response_model=schemas.MessageResponse)
def resend_otp(
    body: schemas.ResendOtpRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Account already verified")

    _send_new_otp(user.email, user.name, db, background_tasks)
    return {"message": "A new OTP has been sent to your email."}


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please verify your OTP first.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": schemas.UserOut.model_validate(user),
    }


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    # Try cache first
    cached = get_user_cache(current_user.id)
    if cached:
        return cached

    user_out = schemas.UserOut.model_validate(current_user)
    set_user_cache(current_user.id, user_out)
    return user_out


# ── Internal helper ───────────────────────────────────────────────────────────

def _send_new_otp(email: str, name: str, db: Session, background_tasks: BackgroundTasks):
    """Invalidate old OTPs, create a new one, and send via background task."""
    # Mark all previous OTPs for this email as used
    db.query(models.OtpVerification).filter(
        models.OtpVerification.email == email,
        models.OtpVerification.is_used == False,
    ).update({"is_used": True})
    db.commit()

    otp = generate_otp()
    otp_record = models.OtpVerification(
        email=email,
        otp_code=otp,
        expires_at=get_otp_expiry(),
        is_used=False,
    )
    db.add(otp_record)
    db.commit()

    background_tasks.add_task(send_otp_email, email, name, otp)
