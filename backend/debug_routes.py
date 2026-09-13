from fastapi import FastAPI
from db.database import engine, Base
from core.config import settings
from app.auth.router import router as auth_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include authentication routes
app.include_router(auth_router)

# Print all routes
print("Registered routes:")
for route in app.routes:
    print(f"  {route.methods} {route.path}")

print("\nAPI Documentation available at: http://localhost:8000/docs")