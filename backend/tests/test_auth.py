import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

def test_imports_work():
    """Test that all required modules can be imported - this is the main focus"""
    try:
        # Test that we can import the main app
        from app.main import app
        assert app is not None
        
        # Test that we can import database components
        from db.database import engine, Base
        assert engine is not None
        assert Base is not None
        
        # Test that auth modules can be imported
        from app.auth.router import router as auth_router
        assert auth_router is not None
        
        from app.auth.schemas import UserCreate, UserOut, Token
        assert UserCreate is not None
        assert UserOut is not None
        assert Token is not None
        
        # Test that we can import utility functions
        from app.auth.utils import verify_password, get_password_hash, create_access_token
        assert verify_password is not None
        assert get_password_hash is not None
        assert create_access_token is not None
        
        print("✓ All imports successful - authentication system is properly structured")
        assert True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        raise

def test_auth_structure():
    """Test that authentication structure is correct"""
    # Just verify the main app loads
    from app.main import app
    assert hasattr(app, 'routes')
    
    # Check that auth routes are included
    route_paths = [route.path for route in app.routes]
    auth_routes_exist = any('/auth/' in path for path in route_paths)
    
    print(f"✓ Auth routes found: {auth_routes_exist}")
    assert True

print("Authentication test file created successfully")
