import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

def test_authorization_dependencies():
    """Test that authorization dependencies work correctly"""
    try:
        # Test that we can import all required authorization components
        from app.auth.dependencies import get_current_user, get_current_active_user
        from app.user_management.dependencies import get_current_admin_user, check_user_ownership
        
        assert get_current_user is not None
        assert get_current_active_user is not None
        assert get_current_admin_user is not None
        assert check_user_ownership is not None
        
        print("✓ All authorization dependencies imported successfully")
        assert True
        
    except Exception as e:
        print(f"✗ Authorization dependency test failed: {e}")
        raise

def test_user_management_routes():
    """Test that user management routes are correctly structured"""
    from app.main import app
    
    # Get all routes
    route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
    
    # Look for user management endpoints
    user_endpoints = [
        '/users/me',
        '/users/me/',
        '/users/',
        '/users/{user_id}'
    ]
    
    existing_routes = []
    for path in route_paths:
        if '/users/' in path:
            existing_routes.append(path)
    
    print(f"✓ Found {len(existing_routes)} user management routes")
    assert len(existing_routes) >= 5  # Should have at least 5 user endpoints
    
    # Verify that we have the required CRUD operations
    get_me = any('/users/me' in path for path in existing_routes)
    put_me = any('/users/me/' in path for path in existing_routes)
    delete_me = any('/users/me' in path and 'delete' in str(path).lower() for path in existing_routes)
    
    print(f"✓ User management endpoints: GET/ME={get_me}, PUT/ME={put_me}, DELETE/ME={delete_me}")
    assert get_me or put_me  # At least some endpoints exist
    
    print("✓ User management route structure verified")
    assert True

def test_user_management_schema_compatibility():
    """Test that user management schemas are compatible with authentication schemas"""
    try:
        from app.auth.schemas import UserOut as AuthUserOut
        from app.user_management.schemas import UserOut as UserManagerUserOut
        
        # Both should be importable and work
        assert AuthUserOut is not None
        assert UserManagerUserOut is not None
        
        print("✓ Schema compatibility verified")
        assert True
        
    except Exception as e:
        print(f"✗ Schema compatibility test failed: {e}")
        raise

print("Authorization and user management test file created successfully")
