#!/usr/bin/env python3
"""
從CNC刪除檔案
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from m70_ezsocket import M70Connection, M70ErrorCode, M70NCType
from m70_ezsocket.m70_giop import M70GIOP


def delete_file():
    """從CNC刪除檔案"""
    # ========================================
    # 設定參數
    # ========================================
    CNC_IP = "192.168.1.206"
    CNC_PORT = 683
    REMOTE_FILE_PATH = "M01:\\PRG\\USER\\O2000.NC"
    
    print("=" * 60)
    print(f"從CNC刪除檔案: {REMOTE_FILE_PATH}")
    print("=" * 60)
    
    # 創建連接
    conn = M70Connection(ip=CNC_IP, port=CNC_PORT, nc_type=M70NCType.MELDAS700M)
    
    print(f"\n1. 連接到CNC: {CNC_IP}:{CNC_PORT}")
    if not conn.connect():
        print("❌ 連接失敗")
        return False
    
    print("✓ 連接成功")
    
    try:
        # ========================================
        # 步驟 2: 檢查檔案是否存在
        # ========================================
        print(f"\n2. 檢查檔案是否存在...")
        
        error_code, file_stat = conn.stat_file(REMOTE_FILE_PATH)
        
        if error_code != M70ErrorCode.OK:
            print(f"⚠ 檔案不存在，無需刪除")
            print(f"  錯誤碼: {error_code} (0x{error_code:08X})")
            return True
        
        file_size = file_stat['file_size']
        print(f"✓ 檔案存在於CNC上")
        print(f"  檔案大小: {file_size} bytes")
        print(f"  修改時間: {file_stat['year']}-{file_stat['month']:02d}-{file_stat['day']:02d} "
              f"{file_stat['hour']:02d}:{file_stat['minute']:02d}:{file_stat['second']:02d}")
        
        # ========================================
        # 步驟 3: 刪除檔案
        # ========================================
        print(f"\n3. 刪除檔案...")
        
        error_code = M70GIOP.mel_fs_remove_file(conn, REMOTE_FILE_PATH)
        
        if error_code != 0:
            print(f"❌ 刪除檔案失敗，錯誤碼: {error_code} (0x{error_code:08X})")
            return False
        
        print(f"✓ 檔案已刪除")
        
        # ========================================
        # 步驟 4: 驗證刪除
        # ========================================
        print(f"\n4. 驗證檔案已刪除...")
        
        error_code, file_stat = conn.stat_file(REMOTE_FILE_PATH)
        
        if error_code != M70ErrorCode.OK:
            print(f"✓ 檔案確實已刪除 (無法找到檔案)")
        else:
            print(f"⚠ 警告: 檔案似乎仍然存在!")
            return False
        
        print(f"\n{'=' * 60}")
        print("✓ 刪除成功!")
        print("=" * 60)
        
        return True
        
    finally:
        conn.disconnect()
        print("\n✓ 連接已關閉")


def main():
    """主函數"""
    delete_file()


if __name__ == "__main__":
    main()
