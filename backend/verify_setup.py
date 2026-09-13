#!/usr/bin/env python3
"""
Simple verification that the setup works correctly.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

def test_imports():
    print("Testing imports...")
    
    try:
        from app.main import app
        print("✓ Main application imported successfully")
        
        from app.auth.router import router as auth_router
        print("✓ Authentication router imported successfully")
        
        from app.user_management.router import router as user_router  
        print("✓ User management router imported successfully")
        
        from app.auth.schemas import UserCreate, UserOut
        print("✓ Authentication schemas imported successfully")
        
        from app.user_management.schemas import UserOut as UserManagerUserOut
        print("✓ User management schemas imported successfully")
        
        # Test that we can access routes
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        user_routes = [p for p in route_paths if '/users/' in p]
        
        print(f"✓ Found {len(user_routes)} user management routes:")
        for route in user_routes:
            print(f"  - {route}")
            
        print("\n🎉 All imports and setup verified successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()
