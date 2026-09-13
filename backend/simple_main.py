#!/usr/bin/env python3
"""Simple test to verify auth routes work"""

from fastapi import FastAPI
from app.auth.router import router as auth_router

# Create simple app
app = FastAPI(title="Test App")

# Include authentication routes  
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Test app running"}

if __name__ == "__main__":
    import uvicorn
    print("Routes available:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.methods} {route.path}")
    print("\nStarting server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)