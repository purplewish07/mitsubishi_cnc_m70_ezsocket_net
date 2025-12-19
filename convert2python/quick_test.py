#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test script - 快速測試腳本
Run this to verify the library works correctly.
運行此腳本以驗證庫是否正常工作。
"""

import sys
import os

# Ensure we can import the library
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic():
    """基本測試"""
    print("=" * 60)
    print("M70 EZSocket Python Library - Quick Test")
    print("三菱CNC M70 EZSocket Python庫 - 快速測試")
    print("=" * 60)
    print()
    
    # Test 1: Import test
    print("測試 1: 導入庫...")
    try:
        from m70_ezsocket import (
            M70Connection, M70Logger, M70LogConfig, 
            M70LogLevel, M70LogTarget, M70NCType, M70ErrorCode
        )
        from m70_ezsocket.typedef import PositionType
        print("✓ 所有模塊導入成功")
    except ImportError as e:
        print(f"✗ 導入失敗: {e}")
        return False
    
    # Test 2: Create connection object
    print("\n測試 2: 創建連接對象...")
    try:
        cnc = M70Connection("192.168.123.130", 683, M70NCType.MELDAS700M)
        print(f"✓ 連接對象創建成功")
        print(f"  - IP: {cnc._ip}")
        print(f"  - Port: {cnc._port}")
        print(f"  - Type: {cnc.nc_type.name}")
    except Exception as e:
        print(f"✗ 創建失敗: {e}")
        return False
    
    # Test 3: Test logger
    print("\n測試 3: 日誌系統...")
    try:
        config = M70LogConfig()
        config.level = M70LogLevel.INFO
        config.target = M70LogTarget.CONSOLE
        M70Logger.init(config)
        M70Logger.info("日誌系統測試消息")
        M70Logger.shutdown()
        print("✓ 日誌系統正常工作")
    except Exception as e:
        print(f"✗ 日誌系統失敗: {e}")
        return False
    
    # Test 4: Test enums
    print("\n測試 4: 枚舉定義...")
    try:
        assert M70ErrorCode.OK == 0
        assert M70NCType.MELDAS700M == 6
        assert PositionType.POS_WRK == 0
        print("✓ 所有枚舉定義正確")
    except AssertionError as e:
        print(f"✗ 枚舉測試失敗: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ 所有測試通過！")
    print("✓ All tests passed!")
    print("=" * 60)
    
    print("\n下一步 (Next Steps):")
    print("1. 修改 examples/simple_example.py 中的IP地址")
    print("   Modify the IP address in examples/simple_example.py")
    print("2. 運行示例: python examples/simple_example.py")
    print("   Run example: python examples/simple_example.py")
    print("3. 查看完整文檔: README.md")
    print("   Check full documentation: README.md")
    
    return True


if __name__ == "__main__":
    try:
        success = test_basic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 測試過程出錯: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
