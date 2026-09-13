#!/usr/bin/env python3
"""Test that all modules can be imported correctly"""

try:
    from app.main import app
    print("✓ main.py imports successfully")
except Exception as e:
    print(f"✗ main.py failed to import: {e}")

try:
    from app.auth.schemas import UserCreate, UserOut, UserLogin, Token
    print("✓ auth schemas imports successfully")
except Exception as e:
    print(f"✗ auth schemas failed to import: {e}")

try:
    from app.auth.utils import verify_password, get_password_hash, create_access_token
    print("✓ auth utils imports successfully")
except Exception as e:
    print(f"✗ auth utils failed to import: {e}")

try:
    from app.auth.dependencies import get_current_user, get_current_active_user
    print("✓ auth dependencies imports successfully")
except Exception as e:
    print(f"✗ auth dependencies failed to import: {e}")

try:
    from db.database import engine, Base, get_db
    print("✓ database imports successfully")
except Exception as e:
    print(f"✗ database failed to import: {e}")

print("Import test completed.")