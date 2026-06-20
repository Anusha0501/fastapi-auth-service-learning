# Production-Style FastAPI Authentication Service

This learning project implements:

- Register user
- Login user with OAuth2 password form
- Refresh token rotation
- Protected `/auth/me` route
- Role-based `/auth/admin` route
- JWT access tokens with scopes
- bcrypt password hashing
- Refresh token hash storage and revocation

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI.

## Learn

- Read `AUTH_NOTES.md` for WHY / WHEN / HOW explanations and Mermaid diagrams.
- Read `INTERVIEW_GUIDE.md` for 100 interview questions.
