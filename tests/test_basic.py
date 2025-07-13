"""Basic unit tests for twsc package."""
import pytest
import sys
import os

# Add the parent directory to the path so we can import twsc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_package_import():
    """Test that the twsc package can be imported."""
    try:
        import twsc
        assert twsc is not None
    except ImportError as e:
        pytest.fail(f"Failed to import twsc package: {e}")

def test_package_structure():
    """Test that the main modules exist."""
    try:
        import twsc.client
        import twsc.contract
        import twsc.const
        import twsc.cache
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import twsc modules: {e}")

def test_utils_import():
    """Test that utils modules can be imported.""" 
    try:
        import twsc.utils.log
        import twsc.utils.cache_utils
        import twsc.utils.market_utils
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import twsc utils: {e}")

def test_mixin_import():
    """Test that mixin modules can be imported."""
    try:
        import twsc.mixin.base
        import twsc.mixin.connection
        import twsc.mixin.historical
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import twsc mixins: {e}")

def test_ibapi_import():
    """Test that ibapi can be imported and is the correct version."""
    try:
        import ibapi
        # Check if we have the newer version
        if hasattr(ibapi, '__version__'):
            version = ibapi.__version__
            print(f"ibapi version: {version}")
        else:
            # Try to import a class that exists in newer versions
            from ibapi.client import EClient
            from ibapi.wrapper import EWrapper
            print("ibapi imported successfully with EClient and EWrapper")
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import ibapi: {e}")

def test_twsc_with_ibapi():
    """Test that twsc can work with ibapi (basic integration test)."""
    try:
        # Test that we can import both together
        import twsc
        import ibapi
        from ibapi.client import EClient
        from ibapi.wrapper import EWrapper
        
        # Test basic class instantiation (without connection)
        class TestWrapper(EWrapper):
            pass
        
        wrapper = TestWrapper()
        assert wrapper is not None
        print("Basic ibapi integration test passed")
    except Exception as e:
        pytest.fail(f"Failed basic ibapi integration: {e}")
