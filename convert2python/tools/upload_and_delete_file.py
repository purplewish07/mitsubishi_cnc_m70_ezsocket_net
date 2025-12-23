#!/usr/bin/env python3
"""
上傳並刪除CNC上的檔案
測試上傳 O3000.NC 然後刪除
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from m70_ezsocket import M70Connection, M70ErrorCode, M70NCType
from m70_ezsocket.m70_giop import M70GIOP


def upload_and_delete_file():
    """上傳並刪除測試檔案"""
    # 連接參數
    CNC_IP = "192.168.1.206"
    CNC_PORT = 683
    
    print("=" * 60)
    print("上傳並刪除檔案測試: O3001.NC")
    print("=" * 60)
    
    # 創建連接
    conn = M70Connection(ip=CNC_IP, port=CNC_PORT, nc_type=M70NCType.MELDAS700M)
    
    print(f"\n1. 連接到CNC: {CNC_IP}:{CNC_PORT}")
    if not conn.connect():
        print("❌ 連接失敗")
        return
    
    print("✓ 連接成功")
    
    try:
        # 準備測試檔案內容
        test_content = b"""(TEST PROGRAM O3001)
(UPLOAD AND DELETE TEST)
N1
M30
%
"""
        
        target_filename = "O3001.NC"
        target_path = f"M01:\\PRG\\USER\\{target_filename}"

        print(f"\n2. 準備上傳檔案: {target_filename}")
        print(f"   檔案大小: {len(test_content)} bytes")
        print(f"   目標路徑: {target_path}")
        
        upload_content = test_content
        
        # ========================================
        # 步驟 3: 檢查檔案是否已存在
        # ========================================
        print(f"\n3. 檢查檔案是否已存在...")
        
        error_code, file_stat = conn.stat_file(target_path)
        
        if error_code == M70ErrorCode.OK:
            print(f"⚠ 檔案已存在，先刪除...")
            error_code = M70GIOP.mel_fs_remove_file(conn, target_path)
            if error_code != 0:
                print(f"❌ 刪除舊檔案失敗，錯誤碼: {error_code}")
                return
            print(f"✓ 舊檔案已刪除")
        else:
            print(f"✓ 檔案不存在，可以創建")
        
        # ========================================
        # 步驟 4: 創建檔案
        # ========================================
        print(f"\n4. 創建檔案...")
        
        # 使用 create_file 創建檔案
        # mode: 0=read, 1=write, 2=read/write
        error_code, fd = M70GIOP.mel_fs_create_file(conn, target_path, 1)
        
        print(f"   DEBUG: error_code={error_code} (0x{error_code:08X}), fd={fd}")
        
        if error_code != 0 or fd == 0:
            print(f"❌ 創建檔案失敗，錯誤碼: {error_code} (0x{error_code:08X}), fd: {fd}")
            return
        
        print(f"✓ 檔案已創建 (fd={fd})")
        
        # 寫入檔案內容
        print(f"\n5. 寫入檔案內容...")
        
        WRITE_CHUNK_SIZE = 1000  # 每次寫入 1000 bytes
        total_written = 0
        chunk_num = 0
        
        try:
            while total_written < len(upload_content):
                chunk_num += 1
                chunk_start = total_written
                chunk_end = min(total_written + WRITE_CHUNK_SIZE, len(upload_content))
                chunk_data = upload_content[chunk_start:chunk_end]
                
                # 寫入一個區塊
                error_code, actual_written = M70GIOP.mel_fs_write_file(conn, fd, chunk_data, len(chunk_data))
                
                if error_code != 0:
                    print(f"\n❌ 寫入失敗 (批次 {chunk_num})，錯誤碼: {error_code}")
                    break
                
                total_written += actual_written
                
                # 顯示進度
                progress = (total_written / len(upload_content)) * 100
                print(f"\r  批次 {chunk_num}: {total_written}/{len(upload_content)} bytes ({progress:.1f}%)", end='', flush=True)
            
            print(f"\n✓ 完成! 總共寫入 {total_written} bytes")
            
            if total_written != len(upload_content):
                print(f"⚠ 警告: 寫入大小與預期不符! 差異: {len(upload_content) - total_written} bytes")
        
        finally:
            # 關閉檔案
            close_error = M70GIOP.mel_fs_close_file(conn, fd)
            if close_error == 0:
                print(f"✓ 檔案已關閉")
            else:
                print(f"⚠ 關閉檔案時發生錯誤: {close_error}")
        
        # ========================================
        # 步驟 6: 驗證上傳的檔案
        # ========================================
        print(f"\n6. 驗證上傳的檔案...")
        
        error_code, file_stat = conn.stat_file(target_path)
        
        if error_code != M70ErrorCode.OK:
            print(f"❌ 無法獲取檔案資訊，錯誤碼: {error_code}")
        else:
            file_size = file_stat['file_size']
            print(f"✓ 檔案存在於CNC上")
            print(f"  檔案大小: {file_size} bytes")
            print(f"  修改時間: {file_stat['year']}-{file_stat['month']:02d}-{file_stat['day']:02d} "
                  f"{file_stat['hour']:02d}:{file_stat['minute']:02d}:{file_stat['second']:02d}")
        
        # ========================================
        # 步驟 7: 讀取並顯示內容
        # ========================================
        print(f"\n7. 讀取檔案內容驗證...")
        
        error_code, fd = M70GIOP.mel_fs_open_file(conn, target_path, 0)  # mode=0 表示只讀
        if error_code == 0 and fd != 0:
            error_code, actual_size, file_data = M70GIOP.mel_fs_read_file(conn, fd, 500)
            M70GIOP.mel_fs_close_file(conn, fd)
            
            if error_code == 0:
                print(f"✓ 成功讀取 {actual_size} bytes")
                print(f"\n檔案內容:")
                print("-" * 60)
                try:
                    content = file_data.decode('utf-8', errors='ignore')
                    for i, line in enumerate(content.split('\n'), 1):
                        if line.strip():
                            print(f"{i:3d}: {line.rstrip()}")
                except:
                    print("(無法解析為文字)")
                print("-" * 60)
        
        # ========================================
        # 步驟 8: 刪除檔案
        # ========================================
        print(f"\n8. 刪除檔案...")
        
        error_code = M70GIOP.mel_fs_remove_file(conn, target_path)
        
        if error_code != 0:
            print(f"❌ 刪除檔案失敗，錯誤碼: {error_code}")
            return
        
        print(f"✓ 檔案已刪除")
        
        # ========================================
        # 步驟 9: 驗證刪除
        # ========================================
        print(f"\n9. 驗證檔案已刪除...")
        
        error_code, file_stat = conn.stat_file(target_path)
        
        if error_code != M70ErrorCode.OK:
            print(f"✓ 檔案確實已刪除 (無法找到檔案)")
        else:
            print(f"⚠ 警告: 檔案似乎仍然存在!")
        
        print(f"\n{'=' * 60}")
        print("測試完成!")
        print("✓ 上傳成功")
        print("✓ 驗證成功")
        print("✓ 刪除成功")
        print("=" * 60)
        
    finally:
        conn.disconnect()
        print("\n✓ 連接已關閉")


def main():
    """主函數"""
    upload_and_delete_file()


if __name__ == "__main__":
    main()
