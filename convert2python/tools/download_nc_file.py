#!/usr/bin/env python3
"""
下載CNC上的NC檔案
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from m70_ezsocket import M70Connection, M70ErrorCode, M70NCType
from m70_ezsocket.m70_giop import M70GIOP


def download_first_nc_file():
    """下載第一個.nc檔案"""
    # 連接參數
    CNC_IP = "192.168.1.214"
    CNC_PORT = 683
    
    print("=" * 60)
    print("下載CNC上的第一個.nc檔案")
    print("=" * 60)
    
    # 創建連接
    conn = M70Connection(ip=CNC_IP, port=CNC_PORT, nc_type=M70NCType.MELDAS700M)
    
    print(f"\n1. 連接到CNC: {CNC_IP}:{CNC_PORT}")
    if not conn.connect():
        print("❌ 連接失敗")
        return
    
    print("✓ 連接成功")
    
    try:
        # 列出 M01:\PRG\USER\ 目錄
        print("\n2. 列出 M01:\\PRG\\USER\\ 目錄...")
        error_code, entries = conn.list_directory("M01:\\PRG\\USER\\", True)
        
        if error_code != M70ErrorCode.OK:
            print(f"❌ 讀取目錄失敗，錯誤碼: {error_code}")
            return
        
        print(f"✓ 找到 {len(entries)} 個項目")
        
        # 列出所有項目
        print("\n目錄內容:")
        for i, entry in enumerate(entries, 1):
            print(f"  {i:2d}. {entry}")
        
        # 尋找第一個.nc或.NC檔案
        # nc_file = "O2000.NC"
        nc_file = None
        for entry in entries:
            if isinstance(entry, str) and entry.upper().endswith('.NC'):
                nc_file = entry
                break
        
        if not nc_file:
            print("❌ 沒有找到.nc檔案")
            print("目錄中的檔案:")
            for entry in entries[:20]:
                print(f"  - {entry}")
            return
        
        print(f"\n3. 找到第一個.nc檔案: {nc_file}")
        
        # 構建完整路徑
        filepath = f"M01:\\PRG\\USER\\{nc_file}"
        
        # 獲取檔案資訊
        print(f"\n4. 獲取檔案資訊...")
        error_code, file_stat = conn.stat_file(filepath)
        
        if error_code != M70ErrorCode.OK:
            print(f"❌ 獲取檔案資訊失敗，錯誤碼: {error_code}")
            return
        
        print(file_stat)
        print(f"{file_stat['mode']:X}")
        file_size = file_stat['file_size']
        print(f"✓ 檔案大小: {file_size} bytes")
        print(f"  修改時間: {file_stat['year']}-{file_stat['month']:02d}-{file_stat['day']:02d} "
              f"{file_stat['hour']:02d}:{file_stat['minute']:02d}:{file_stat['second']:02d}")
        
        # 決定讀取策略
        # CNC 每次最多返回 1000 bytes,所以使用更小的區塊
        CHUNK_SIZE = 1000  # 每次讀取 1000 bytes (CNC限制)
        
        if file_size <= CHUNK_SIZE:
            print(f"\n5. 檔案較小 ({file_size} bytes)，一次性讀取...")
            read_strategy = "single"
        else:
            print(f"\n5. 檔案較大 ({file_size} bytes)，建議分批讀取")
            print(f"   每批次: {CHUNK_SIZE} bytes")
            print(f"   預估批次數: {(file_size + CHUNK_SIZE - 1) // CHUNK_SIZE}")
            read_strategy = "chunked"
        
        # 讀取檔案內容
        print(f"\n開始下載...")
        
        if read_strategy == "single":
            # 小檔案：一次性讀取
            error_code, file_data = conn.read_file(filepath, max_size=file_size + 1024)
            
            if error_code != M70ErrorCode.OK:
                print(f"❌ 讀取檔案失敗，錯誤碼: {error_code}")
                return
            
            print(f"✓ 成功讀取 {len(file_data)} bytes")
            
        else:
            # 大檔案：分批讀取
            file_data = bytearray()
            
            # 打開檔案
            error_code, fd = M70GIOP.mel_fs_open_file(conn, filepath, 0)  # mode=0 表示只讀
            if error_code != 0 or fd == 0:
                print(f"❌ 無法打開檔案，錯誤碼: {error_code}")
                return
            
            print(f"✓ 檔案已打開 (fd={fd})")
            
            try:
                total_read = 0
                chunk_num = 0
                
                while total_read < file_size:
                    chunk_num += 1
                    need_read = min(CHUNK_SIZE, file_size - total_read)
                    
                    # 讀取一個區塊
                    error_code, actual_size, chunk_data = M70GIOP.mel_fs_read_file(conn, fd, need_read)
                    
                    if error_code != 0:
                        print(f"\n❌ 讀取失敗 (批次 {chunk_num})，錯誤碼: {error_code}")
                        break
                    
                    if actual_size == 0:
                        print(f"\n⚠ 到達檔案結尾 (批次 {chunk_num})")
                        break
                    
                    file_data.extend(chunk_data)
                    total_read += actual_size
                    
                    # 顯示進度
                    progress = (total_read / file_size) * 100
                    print(f"\r  批次 {chunk_num}: {total_read}/{file_size} bytes ({progress:.1f}%)", end='', flush=True)
                    
                    # 如果讀取的數據少於請求的，繼續嘗試讀取剩餘部分
                    if actual_size < need_read:
                        # 可能是接近檔案結尾，或是網路問題，繼續嘗試
                        pass
                
                print(f"\n✓ 完成! 總共讀取 {total_read} bytes (預期 {file_size} bytes)")
                
                if total_read != file_size:
                    print(f"⚠ 警告: 讀取大小與檔案大小不符! 差異: {file_size - total_read} bytes")
                
                file_data = bytes(file_data)
                
            finally:
                # 關閉檔案
                close_error = M70GIOP.mel_fs_close_file(conn, fd)
                if close_error == 0:
                    print(f"✓ 檔案已關閉")
                else:
                    print(f"⚠ 關閉檔案時發生錯誤: {close_error}")
        
        # 儲存到本地
        output_dir = os.path.join(os.path.dirname(__file__), "downloads")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, nc_file)
        
        print(f"\n6. 儲存到本地: {output_file}")
        
        # # 檢查是否為NC檔案,如果是且開頭不是%,則自動添加
        # if nc_file.upper().endswith('.NC') and len(file_data) > 0 and file_data[0:1] != b'%':
        #     print(f"   ⚠ 偵測到NC檔案缺少開頭的 % 符號，自動添加...")
        #     file_data = b'%\r\n' + file_data
        
        with open(output_file, 'wb') as f:
            f.write(file_data)
        
        print(f"✓ 檔案已儲存 ({len(file_data)} bytes)")
        
        # 驗證檔案大小
        saved_size = os.path.getsize(output_file)
        if saved_size == len(file_data):
            print(f"✓ 檔案大小驗證成功: {saved_size} bytes")
        else:
            print(f"⚠ 警告: 儲存的檔案大小不符 (saved={saved_size}, expected={len(file_data)})")
        
        # 顯示檔案內容預覽
        print(f"\n7. 檔案內容預覽:")
        print("=" * 60)
        try:
            content = file_data.decode('utf-8', errors='ignore')
            lines = content.split('\n')
            
            # 顯示前20行
            for i, line in enumerate(lines[:20], 1):
                print(f"{i:3d}: {line.rstrip()}")
            
            if len(lines) > 20:
                print(f"... (還有 {len(lines) - 20} 行)")
            
            print("=" * 60)
            print(f"\n✓ 總共 {len(lines)} 行")
            
        except Exception as e:
            print(f"(無法解析為文字檔案: {e})")
            # 顯示前512 bytes的hex dump
            print("Hex dump (前512 bytes):")
            for i in range(0, min(512, len(file_data)), 16):
                hex_str = ' '.join(f'{b:02X}' for b in file_data[i:i+16])
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in file_data[i:i+16])
                print(f"{i:04X}: {hex_str:<48} {ascii_str}")
        
    finally:
        conn.disconnect()
        print("\n✓ 連接已關閉")


def main():
    """主函數"""
    download_first_nc_file()


if __name__ == "__main__":
    main()
