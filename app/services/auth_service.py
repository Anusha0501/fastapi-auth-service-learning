from datetime import UTC, datetime, timedelta
import hashlib

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate


def scopes_for_role(role: UserRole) -> list[str]:
    scopes = ["users:read"]
    if role == UserRole.admin:
        scopes.extend(["users:write", "admin:read"])
    return scopes


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def register_user(db: Session, payload: UserCreate) -> User:
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=payload.email.lower(), hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def issue_token_pair(db: Session, user: User) -> tuple[str, str]:
    settings = get_settings()
    scopes = scopes_for_role(user.role)
    access_token = create_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access",
        scopes=scopes,
    )
    refresh_token = create_token(
        subject=str(user.id),
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        token_type="refresh",
        scopes=[],
    )
    db.add(
        RefreshToken(
            token_hash=digest_token(refresh_token),
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    db.commit()
    return access_token, refresh_token


def refresh_access_token(db: Session, refresh_token: str) -> tuple[str, str]:
    claims = decode_token(refresh_token)
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expected refresh token")
    token_row = db.query(RefreshToken).filter(RefreshToken.token_hash == digest_token(refresh_token)).first()
    if not token_row or token_row.revoked or token_row.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    user = db.get(User, int(claims["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer active")
    token_row.revoked = True
    db.commit()
    return issue_token_pair(db, user)
