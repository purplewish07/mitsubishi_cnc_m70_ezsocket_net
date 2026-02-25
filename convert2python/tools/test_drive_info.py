#!/usr/bin/env python3
"""
Test GetDriveInformation using mel_get_data with different parameters
Based on packet analysis: mochaGetData(section=2, subsection=100, system_no=0, axis_flag=?, data_type=T_CHAR)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from m70_ezsocket import M70Connection, M70NCType
from m70_ezsocket.typedef import M70DataType


def test_drive_info():
    """Test various parameters to get drive information"""
    
    # Connect to CNC
    cnc = M70Connection(ip="192.168.1.214", port=683, nc_type=M70NCType.MELDAS700M)
    
    print("=" * 60)
    print("Test GetDriveInformation using mel_get_data")
    print("=" * 60)
    print()
    
    if not cnc.connect():
        print("ERROR: Failed to connect to CNC")
        return
    
    print("✓ Connected to CNC")
    print()
    
    # Test 1: Original read_nc_type parameters
    print("Test 1: section=2, subsection=100, system_no=0, axis_flag=0")
    ret, data = cnc._mel_get_data(2, 100, 0, 0, M70DataType.T_CHAR)
    print(f"  Return: {ret}")
    print(f"  Data: {data} (0x{data:02X})")
    print(f"  Type: {'LATHE' if (data & 0xFF) == 1 else 'MC'}")
    print()
    
    # Test 2: Try with axis_flag=1 ★ FROM PACKET
    print("Test 2: section=2, subsection=100, system_no=0, axis_flag=1 ★ FROM WIRESHARK")
    ret, data = cnc._mel_get_data(2, 100, 0, 1, M70DataType.T_CHAR)
    print(f"  Return: {ret}")
    print(f"  Data: {data} (0x{data:02X})")
    if ret == 0:
        print(f"  → This is the EXACT packet captured in File_GetDriveInformation()")
        print(f"  → GIOP Reply: return=0, but NO string data!")
    print()
    
    # Test 3: Try with different axis_flag values
    print("Test 3: Testing different axis_flag values (0, 1, 2, 3)")
    for flag in [0, 1, 2, 3]:
        ret, data = cnc._mel_get_data(2, 100, 0, flag, M70DataType.T_CHAR)
        print(f"  axis_flag={flag}: ret={ret}, data={data} (0x{data:02X})")
    print()
    
    # Test 4: Try reading as STRING type instead of CHAR
    print("Test 4: section=2, subsection=100, system_no=0, axis_flag=0, T_STR")
    ret, data = cnc._mel_get_data(2, 100, 0, 0, M70DataType.T_STR)
    print(f"  Return: {ret}")
    if isinstance(data, bytes):
        print(f"  Data (hex): {data.hex()}")
        print(f"  Data (str): {data.decode('utf-8', errors='ignore').rstrip(chr(0))}")
    else:
        print(f"  Data: {data}")
    print()
    
    # Test 5: Try with different subsections
    print("Test 5: Exploring other subsections around 100")
    for subsection in [99, 100, 101, 102]:
        ret, data = cnc._mel_get_data(2, subsection, 0, 0, M70DataType.T_CHAR)
        print(f"  subsection={subsection}: ret={ret}, data={data} (0x{data:02X})")
    print()
    
    # Test 6: Try to mimic File_GetDriveInformation exactly as seen in packet
    print("Test 6: Exact packet parameters from Wireshark")
    print("  Wireshark shows: mochaGetData(2, 100, 0, 1, T_CHAR)")
    print("  Reply contains: return=0, two int32 values (1, 1), end byte")
    print("  But NO STRING DATA in GIOP packets!")
    ret, data = cnc._mel_get_data(2, 100, 0, 1, M70DataType.T_CHAR)
    print(f"  Return: {ret}")
    print(f"  Data: {data}")
    print()
    print("  Analysis: The string 'M01:\\r\\n' is NOT transmitted via GIOP.")
    print("  EZCOM.dll likely uses shared memory or another mechanism.")
    print()
    
    # Test 7: Check if reply contains memory address or handle
    print("Test 7: Read as different data types to see what's returned")
    for dtype_name, dtype_value in [
        ("T_CHAR", M70DataType.T_CHAR),
        ("T_SHORT", M70DataType.T_SHORT),
        ("T_LONG", M70DataType.T_LONG),
        ("T_DLONG", M70DataType.T_DLONG)
    ]:
        ret, data = cnc._mel_get_data(2, 100, 0, 1, dtype_value)
        print(f"  {dtype_name}: ret={ret}, data={data} (0x{data:X})")
    print()
    
    # Disconnect
    cnc.disconnect()
    print("✓ Disconnected")
    print()
    
    print("=" * 60)
    print("Analysis:")
    print("=" * 60)
    print("Based on the Wireshark capture, File_GetDriveInformation")
    print("sends: mochaGetData(2, 100, 0, 1) and receives a reply")
    print("with return_code=0, param1=1, param2=1.")
    print()
    print("The string 'M01:\\r\\n' is NOT in the GIOP packets!")
    print("This suggests EZCOM uses shared memory or another IPC")
    print("mechanism to transfer the actual drive information string.")
    print()


if __name__ == "__main__":
    try:
        test_drive_info()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
