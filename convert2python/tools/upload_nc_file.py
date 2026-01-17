#!/usr/bin/env python3
"""
上傳檔案到CNC
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from m70_ezsocket import M70Connection, M70ErrorCode, M70NCType
from m70_ezsocket.m70_giop import M70GIOP


def upload_file():
    """上傳檔案到CNC"""
    # ========================================
    # 設定參數
    # ========================================
    CNC_IP = "192.168.1.206"
    CNC_PORT = 683
    LOCAL_FILE_PATH = ".\\downloads\\O3000.NC"
    REMOTE_FILE_PATH = "M01:\\PRG\\USER\\O3000.NC"
    
    print("=" * 60)
    print(f"上傳檔案到CNC: {REMOTE_FILE_PATH}")
    print("=" * 60)
    
    # 讀取本地檔案
    try:
        with open(LOCAL_FILE_PATH, 'rb') as f:
            file_content = f.read()
        print(f"\n✓ 讀取本地檔案: {LOCAL_FILE_PATH}")
        print(f"  檔案大小: {len(file_content)} bytes")
    except Exception as e:
        print(f"❌ 無法讀取本地檔案: {e}")
        return False
    
    # 創建連接
    conn = M70Connection(ip=CNC_IP, port=CNC_PORT, nc_type=M70NCType.MELDAS700M)
    
    print(f"\n1. 連接到CNC: {CNC_IP}:{CNC_PORT}")
    if not conn.connect():
        print("❌ 連接失敗")
        return False
    
    print("✓ 連接成功")
    
    try:
        # ========================================
        # 步驟 2: 檢查檔案是否已存在
        # ========================================
        print(f"\n2. 檢查目標檔案是否已存在...")
        
        error_code, file_stat = conn.stat_file(REMOTE_FILE_PATH)
        
        if error_code == M70ErrorCode.OK:
            print(f"⚠ 檔案已存在，先刪除...")
            error_code = M70GIOP.mel_fs_remove_file(conn, REMOTE_FILE_PATH)
            if error_code != 0:
                print(f"❌ 刪除舊檔案失敗，錯誤碼: {error_code} (0x{error_code:08X})")
                return False
            print(f"✓ 舊檔案已刪除")
        else:
            print(f"✓ 檔案不存在，可以創建")
        
        # ========================================
        # 步驟 3: 創建檔案
        # ========================================
        print(f"\n3. 創建檔案...")
        
        # 使用 create_file 創建檔案
        # mode: 0=read, 1=write, 2=read/write
        error_code, fd = M70GIOP.mel_fs_create_file(conn, REMOTE_FILE_PATH, 1)
        
        if error_code != 0 or fd == 0:
            print(f"❌ 創建檔案失敗，錯誤碼: {error_code} (0x{error_code:08X}), fd: {fd}")
            return False
        
        print(f"✓ 檔案已創建 (fd={fd})")
        
        # ========================================
        # 步驟 4: 寫入檔案內容
        # ========================================
        print(f"\n4. 寫入檔案內容...")
        
        WRITE_CHUNK_SIZE = 1000  # 每次寫入 1000 bytes
        total_written = 0
        chunk_num = 0
        
        try:
            while total_written < len(file_content):
                chunk_num += 1
                chunk_start = total_written
                chunk_end = min(total_written + WRITE_CHUNK_SIZE, len(file_content))
                chunk_data = file_content[chunk_start:chunk_end]
                
                # 寫入一個區塊
                error_code, actual_written = M70GIOP.mel_fs_write_file(conn, fd, chunk_data, len(chunk_data))
                
                if error_code != 0:
                    print(f"\n❌ 寫入失敗 (批次 {chunk_num})，錯誤碼: {error_code} (0x{error_code:08X})")
                    return False
                
                total_written += actual_written
                
                # 顯示進度
                progress = (total_written / len(file_content)) * 100
                print(f"\r  批次 {chunk_num}: {total_written}/{len(file_content)} bytes ({progress:.1f}%)", end='', flush=True)
            
            print(f"\n✓ 完成! 總共寫入 {total_written} bytes")
            
            if total_written != len(file_content):
                print(f"⚠ 警告: 寫入大小與預期不符! 差異: {len(file_content) - total_written} bytes")
                return False
        
        finally:
            # 關閉檔案
            close_error = M70GIOP.mel_fs_close_file(conn, fd)
            if close_error == 0:
                print(f"✓ 檔案已關閉")
            else:
                print(f"⚠ 關閉檔案時發生錯誤: {close_error}")
        
        # ========================================
        # 步驟 5: 驗證上傳的檔案
        # ========================================
        print(f"\n5. 驗證上傳的檔案...")
        
        error_code, file_stat = conn.stat_file(REMOTE_FILE_PATH)
        
        if error_code != M70ErrorCode.OK:
            print(f"❌ 無法獲取檔案資訊，錯誤碼: {error_code} (0x{error_code:08X})")
            return False
        
        file_size = file_stat['file_size']
        print(f"✓ 檔案存在於CNC上")
        print(f"  檔案大小: {file_size} bytes")
        print(f"  修改時間: {file_stat['year']}-{file_stat['month']:02d}-{file_stat['day']:02d} "
              f"{file_stat['hour']:02d}:{file_stat['minute']:02d}:{file_stat['second']:02d}")
        
        if file_size != len(file_content):
            print(f"⚠ 警告: CNC上的檔案大小 ({file_size}) 與本地檔案 ({len(file_content)}) 不符!")
            return False
        
        print(f"\n{'=' * 60}")
        print("✓ 上傳成功!")
        print("=" * 60)
        
        return True
        
    finally:
        conn.disconnect()
        print("\n✓ 連接已關閉")


def main():
    """主函數"""
    upload_file()


if __name__ == "__main__":
    main()
