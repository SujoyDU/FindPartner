from fastapi import FastAPI
from db.database import engine, Base
from core.config import settings
from app.auth.router import router as auth_router
from app.user_management.router import router as user_management_router
from app.admin.router import router as admin_router
from app.media.router import router as media_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include authentication routes
app.include_router(auth_router)

# Include user management routes
app.include_router(user_management_router)

# Include admin routes
app.include_router(admin_router)

# Include media management routes
app.include_router(media_router)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Welcome to FindPartner API"}
