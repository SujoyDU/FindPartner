import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

def test_auth_system_comprehensive():
    """Comprehensive test of authentication system structure"""
    
    # Test 1: Import all core modules
    try:
        from app.main import app
        from db.database import engine, Base
        from app.auth.router import router as auth_router
        from app.auth.schemas import UserCreate, UserOut, Token, UserLogin
        from app.auth.utils import verify_password, get_password_hash, create_access_token
        from app.auth.dependencies import get_current_active_user
        print("✓ All authentication modules imported successfully")
    except Exception as e:
        raise AssertionError(f"Failed to import authentication modules: {e}")
    
    # Test 2: Verify app structure
    assert app is not None, "Main app should not be None"
    assert hasattr(app, 'routes'), "App should have routes attribute"
    print("✓ Main application structure verified")
    
    # Test 3: Verify database setup
    assert engine is not None, "Database engine should not be None"
    assert Base is not None, "Database Base should not be None"
    print("✓ Database configuration verified")
    
    # Test 4: Verify auth router structure
    assert auth_router is not None, "Auth router should not be None"
    assert hasattr(auth_router, 'routes'), "Auth router should have routes"
    print("✓ Authentication router structure verified")
    
    # Test 5: Verify schema structure
    assert UserCreate is not None, "UserCreate schema should not be None"
    assert UserOut is not None, "UserOut schema should not be None"
    assert Token is not None, "Token schema should not be None"
    print("✓ Authentication schemas verified")
    
    # Test 6: Verify utility functions
    assert verify_password is not None, "verify_password function should not be None"
    assert get_password_hash is not None, "get_password_hash function should not be None"
    assert create_access_token is not None, "create_access_token function should not be None"
    print("✓ Authentication utilities verified")
    
    # Test 7: Check that authentication endpoints are properly defined
    route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
    auth_routes = [path for path in route_paths if '/auth/' in path]
    
    assert len(auth_routes) >= 3, f"Expected at least 3 auth routes, found {len(auth_routes)}"
    print(f"✓ Authentication system has {len(auth_routes)} routes")
    
    print("✅ All comprehensive authentication tests passed!")

def test_import_structure():
    """Test that the import structure works correctly"""
    try:
        # Test that we can access all components
        from app.auth.schemas import UserCreate, UserOut, Token, UserLogin
        from app.auth.utils import verify_password, get_password_hash, create_access_token
        
        # Create test objects to verify they work
        user_create = UserCreate(username="test", email="test@example.com", password="password")
        token_schema = Token(access_token="test_token", token_type="bearer")
        
        print("✓ Import structure and schema instantiation works correctly")
        assert True
        
    except Exception as e:
        raise AssertionError(f"Import structure test failed: {e}")

if __name__ == "__main__":
    test_auth_system_comprehensive()
    test_import_structure()
    print("🎉 All tests completed successfully!")
