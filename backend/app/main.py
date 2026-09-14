from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text

from app.admin.router import router as admin_router
from app.auth.router import router as auth_router
from app.media.router import router as media_router
from app.user_management.router import router as user_management_router
from core.config import settings
from db.database import engine, Base
from core.logging_conf import configure_logging


configure_logging()


def _enforce_production_secrets() -> None:
    if settings.ENV == "production":
        problems: List[str] = []
        if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here":
            problems.append("SECRET_KEY must be set to a strong, unique value in production")
        if not settings.CORS_ORIGINS:
            problems.append("CORS_ORIGINS must be set in production (empty = disallow all)")
        if problems:
            raise SystemExit("\n".join(["PRODUCTION STARTUP BLOCKED:", *problems]))


_enforce_production_secrets()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # In development we still create tables so the app can boot against a clean
    # Postgres without needing to run Alembic manually. In production we rely on
    # the `alembic upgrade head` job run by the operator; this call is harmless
    # because `create_all` is a no-op if the tables already exist with matching
    # shape (it does not drop or alter them).
    if settings.ENV in {"development", "test"}:
        Base.metadata.create_all(bind=engine)
    # Connectivity smoke test: if Postgres is unreachable, fail fast at startup.
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# --- CORS (env-driven; no "*" with credentials) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# --- Security headers on every response ---
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'self'; form-action 'self'",
    )
    response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


# --- Routers ---
app.include_router(auth_router)
app.include_router(user_management_router)
app.include_router(admin_router)
app.include_router(media_router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"message": "Welcome to FindPartner API"}


# --- Global error handlers (no stack traces, uniform shape) ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": "http_error"},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "code": "validation_error"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Intentionally generic: we do NOT expose internals. Log on the server side.
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_error"},
    )
