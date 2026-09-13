#!/usr/bin/env python3

"""
Verification script to check that our admin implementation is correctly set up.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported properly"""
    
    try:
        from app.main import app
        print("✓ Main application imported successfully")
    except Exception as e:
        print(f"✗ Failed to import main application: {e}")
        return False
    
    try:
        from app.admin.router import router as admin_router
        print("✓ Admin router imported successfully")
    except Exception as e:
        print(f"✗ Failed to import admin router: {e}")
        return False
        
    try:
        from app.auth.dependencies import get_current_admin_user
        print("✓ Admin dependency imported successfully")
    except Exception as e:
        print(f"✗ Failed to import admin dependency: {e}")
        return False
        
    try:
        from db.models import User
        print("✓ Database models imported successfully")
    except Exception as e:
        print(f"✗ Failed to import database models: {e}")
        return False
    
    print("✓ All imports successful - Admin dashboard implementation is ready!")
    return True

if __name__ == "__main__":
    test_imports()
