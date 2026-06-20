from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scopes={
        "users:read": "Read the current user profile",
        "users:write": "Modify user records",
        "admin:read": "Read administrative data",
    },
)


def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        claims = decode_token(token)
    except ValueError as exc:
        raise credentials_exception from exc
    if claims.get("type") != "access" or not claims.get("sub"):
        raise credentials_exception
    token_scopes = set(claims.get("scopes", []))
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    user = db.get(User, int(claims["sub"]))
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_admin(current_user: User = Security(get_current_user, scopes=["admin:read"])) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user
