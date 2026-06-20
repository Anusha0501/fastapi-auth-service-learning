from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Production-Style Authentication Service",
    description="Learning project for JWT access tokens, refresh tokens, OAuth2 scopes, and RBAC.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
