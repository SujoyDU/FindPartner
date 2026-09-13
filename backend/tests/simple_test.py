import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

def test_imports():
    """Simple test to verify imports work"""
    try:
        from app.main import app
        from db.database import engine, Base
        print("✓ All imports successful")
        assert True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        assert False, f"Import failed: {e}"

def test_basic_functionality():
    """Test that basic functionality works"""
    # Just make sure we can import and access the main app
    from app.main import app
    assert app is not None
    print("✓ Basic app import successful")
    assert True
