from fastapi import APIRouter, Depends, Security
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.auth import RefreshRequest, TokenPair, UserCreate, UserRead
from app.services.auth_service import authenticate_user, issue_token_pair, refresh_access_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    return register_user(db, payload)


@router.post("/login", response_model=TokenPair)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenPair:
    user = authenticate_user(db, form.username, form.password)
    access_token, refresh_token = issue_token_pair(db, user)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    access_token, refresh_token = refresh_access_token(db, payload.refresh_token)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Security(get_current_user, scopes=["users:read"])) -> User:
    return current_user


@router.get("/admin")
def admin_dashboard(current_user: User = Depends(require_admin)) -> dict[str, str]:
    return {"message": f"Welcome admin {current_user.email}"}
