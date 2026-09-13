import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

def test_user_management_imports():
    """Test that all user management modules can be imported"""
    try:
        # Test that we can import the main app with user management
        from app.main import app
        assert app is not None
        
        # Test that we can import user management components
        from app.user_management.router import router as user_router
        assert user_router is not None
        
        from app.user_management.schemas import UserCreate, UserOut, UserUpdate, UserDeactivate
        assert UserCreate is not None
        assert UserOut is not None
        assert UserUpdate is not None
        assert UserDeactivate is not None
        
        # Test that we can import dependencies
        from app.user_management.dependencies import get_current_admin_user, check_user_ownership
        assert get_current_admin_user is not None
        assert check_user_ownership is not None
        
        print("✓ All user management modules imported successfully")
        assert True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        raise

def test_user_management_structure():
    """Test that user management routes are properly defined"""
    from app.main import app
    
    # Check that we have the expected routes
    route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
    
    # Authentication routes should exist
    auth_routes = [path for path in route_paths if '/auth/' in path]
    assert len(auth_routes) >= 3, f"Expected at least 3 auth routes, found {len(auth_routes)}"
    
    # User management routes should exist
    user_routes = [path for path in route_paths if '/users/' in path]
    assert len(user_routes) >= 5, f"Expected at least 5 user routes, found {len(user_routes)}"
    
    print(f"✓ User management system has {len(user_routes)} routes")
    assert True

def test_user_schemas():
    """Test that user schemas are properly structured"""
    try:
        from app.user_management.schemas import UserCreate, UserOut, UserUpdate, UserDeactivate
        
        # Test that we can create instances of the schemas
        user_create = UserCreate(username="testuser", email="test@example.com", password="password123")
        assert user_create.username == "testuser"
        assert user_create.email == "test@example.com"
        
        user_update = UserUpdate(username="updateduser")
        assert user_update.username == "updateduser"
        
        user_deactivate = UserDeactivate(is_active=False)
        assert user_deactivate.is_active is False
        
        print("✓ User schemas work correctly")
        assert True
        
    except Exception as e:
        print(f"✗ Schema test failed: {e}")
        raise

print("User management test file created successfully")
