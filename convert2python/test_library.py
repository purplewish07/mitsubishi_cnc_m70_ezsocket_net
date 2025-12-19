"""
Test script to verify the M70 EZSocket Python library
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m70_ezsocket import (
    M70Connection, M70Logger, M70LogConfig, M70LogLevel, M70LogTarget,
    M70NCType, M70ErrorCode
)
from m70_ezsocket.typedef import PositionType


def test_import():
    """Test if all modules can be imported"""
    print("✓ All modules imported successfully")


def test_connection_creation():
    """Test connection object creation"""
    cnc = M70Connection("192.168.123.130", 683, M70NCType.MELDAS700M)
    assert cnc._ip == "192.168.123.130"
    assert cnc._port == 683
    assert cnc.nc_type == M70NCType.MELDAS700M
    print("✓ Connection object created successfully")


def test_logger():
    """Test logging system"""
    config = M70LogConfig()
    config.level = M70LogLevel.INFO
    config.target = M70LogTarget.CONSOLE
    
    result = M70Logger.init(config)
    assert result == True
    
    M70Logger.info("Test log message")
    M70Logger.warning("Test warning message")
    M70Logger.error("Test error message")
    
    M70Logger.shutdown()
    print("✓ Logging system works correctly")


def test_enums():
    """Test enum definitions"""
    assert M70ErrorCode.OK == 0
    assert M70NCType.MELDAS700M == 6
    assert PositionType.POS_WRK == 0
    print("✓ Enum definitions are correct")


def main():
    """Run all tests"""
    print("Running M70 EZSocket Python Library Tests...\n")
    
    try:
        test_import()
        test_connection_creation()
        test_logger()
        test_enums()
        
        print("\n" + "="*50)
        print("All tests passed! ✓")
        print("="*50)
        print("\nNote: Connection tests require actual CNC hardware.")
        print("To test with real hardware, use examples/simple_example.py")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
