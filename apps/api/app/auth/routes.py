from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    UserOut,
    VerifyEmailRequest,
)
from app.core.config import get_settings
from app.core.deps import CurrentUser, get_current_user
from app.core.email import send_password_reset_email
from app.core.rate_limit import is_rate_limited
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.organizations.models import Organization
from app.users.models import EmailVerificationToken, PasswordResetToken, RefreshSession, RoleName, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()

GENERIC_AUTH_ERROR = "Invalid email or password"  # never reveal which part was wrong (anti-enumeration)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # Omit the `domain` attribute entirely when unset/"localhost" - explicitly setting
    # domain="localhost" causes browsers (and some HTTP clients, e.g. in tests) to reject
    # the cookie unless the request host is exactly "localhost". Letting the browser
    # default to "current host" is both simpler and more portable across environments.
    cookie_domain = settings.COOKIE_DOMAIN if settings.COOKIE_DOMAIN not in ("", "localhost") else None

    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="none",
        domain=cookie_domain,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="none",
        domain=cookie_domain,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        # Generic message to avoid confirming which emails already exist elsewhere;
        # here we do need to tell the user registration failed, but keep it generic.
        raise HTTPException(status_code=400, detail="Unable to register with the provided details")

    # Auto-assign organization so volunteers/beneficiaries land in the right NGO.
    # In a production multi-NGO setup, the registration form would let users choose.
    org_id = payload.organization_id
    if not org_id and payload.role in (RoleName.NGO_ADMIN, RoleName.VOLUNTEER, RoleName.BENEFICIARY):
        org = await db.scalar(select(Organization).limit(1))
        if org:
            org_id = org.id

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        organization_id=org_id,
        is_email_verified=True,
    )
    db.add(user)
    await db.flush()

    db.add(
        AuditLog(actor_id=user.id, action="user.registered", resource_type="user", resource_id=str(user.id))
    )
    await db.commit()

    return user


@router.post("/verify-email")
async def verify_email(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_opaque_token(payload.token)
    result = await db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()
    if not record or record.used_at is not None or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    result = await db.execute(select(User).where(User.id == record.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user.is_email_verified = True
    record.used_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Email verified successfully"}


@router.post("/login", response_model=UserOut)
async def login(
    payload: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"login:{client_ip}", settings.LOGIN_RATE_LIMIT_PER_MINUTE, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again shortly.",
        )

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    user.failed_login_attempts = 0
    user.locked_until = None

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    access_token = create_access_token(
        user.id, user.role.value, str(user.organization_id) if user.organization_id else None
    )
    raw_refresh = generate_opaque_token()
    db.add(
        RefreshSession(
            user_id=user.id,
            token_hash=hash_opaque_token(raw_refresh),
            user_agent=request.headers.get("user-agent"),
            ip_address=client_ip,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    db.add(AuditLog(actor_id=user.id, action="user.login", resource_type="user", resource_id=str(user.id)))
    await db.commit()

    _set_auth_cookies(response, access_token, raw_refresh)
    return user


@router.post("/refresh", response_model=UserOut)
async def refresh(
    response: Response,
    request: Request,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token_hash = hash_opaque_token(refresh_token)
    result = await db.execute(select(RefreshSession).where(RefreshSession.token_hash == token_hash))
    session = result.scalar_one_or_none()

    if not session or session.revoked_at is not None or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please log in again"
        )

    result = await db.execute(select(User).where(User.id == session.user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Rotate: revoke old refresh session, issue a new one (prevents replay of stolen tokens)
    session.revoked_at = datetime.now(timezone.utc)
    new_raw_refresh = generate_opaque_token()
    db.add(
        RefreshSession(
            user_id=user.id,
            token_hash=hash_opaque_token(new_raw_refresh),
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else "unknown",
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    await db.commit()

    access_token = create_access_token(
        user.id, user.role.value, str(user.organization_id) if user.organization_id else None
    )
    _set_auth_cookies(response, access_token, new_raw_refresh)
    return user


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if refresh_token:
        token_hash = hash_opaque_token(refresh_token)
        result = await db.execute(select(RefreshSession).where(RefreshSession.token_hash == token_hash))
        session = result.scalar_one_or_none()
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            await db.commit()

    cookie_domain = settings.COOKIE_DOMAIN if settings.COOKIE_DOMAIN not in ("", "localhost") else None
    response.delete_cookie("access_token", domain=cookie_domain)
    response.delete_cookie("refresh_token", domain=cookie_domain, path="/api/v1/auth")
    return {"message": "Logged out"}


@router.post("/logout-all")
async def logout_all(
    current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RefreshSession).where(
            RefreshSession.user_id == current_user.id, RefreshSession.revoked_at.is_(None)
        )
    )
    for session in result.scalars().all():
        session.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Logged out from all devices"}


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user.id))
    return result.scalar_one()


@router.patch("/me", response_model=UserOut)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    db.add(
        AuditLog(
            actor_id=user.id, action="user.password_changed", resource_type="user", resource_id=str(user.id)
        )
    )
    await db.commit()
    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    # Always return the same generic response whether or not the email exists (anti-enumeration)
    if user:
        raw_token = generate_opaque_token()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        await db.commit()
        send_password_reset_email(user.email, raw_token)
    return {"message": "If an account exists for this email, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_opaque_token(payload.token)
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    record = result.scalar_one_or_none()
    if not record or record.used_at is not None or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    result = await db.execute(select(User).where(User.id == record.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.password_hash = hash_password(payload.new_password)
    record.used_at = datetime.now(timezone.utc)

    # Revoke all existing sessions on password reset (security best practice)
    result = await db.execute(
        select(RefreshSession).where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))
    )
    for session in result.scalars().all():
        session.revoked_at = datetime.now(timezone.utc)

    await db.commit()
    return {"message": "Password reset successfully. Please log in again."}
