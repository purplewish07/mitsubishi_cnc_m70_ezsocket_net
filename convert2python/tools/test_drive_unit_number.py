#!/usr/bin/env python3
"""
Test hypothesis: GIOP returns NC control unit number, EZCOM formats it as "M01:"
Based on Wireshark analysis showing param1=1, param2=1 in reply
"""

import sys
import os
import struct

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from m70_ezsocket import M70Connection, M70NCType
from m70_ezsocket.typedef import M70DataType
from m70_ezsocket.m70_socket import M70Socket


def parse_raw_response(cnc):
    """
    Manually parse the GIOP response to see ALL returned values
    This bypasses the normal parsing to see raw data
    """
    print("Sending raw GIOP request for mochaGetData(2, 100, 0, 1)...")
    
    # Build request (same as _mel_get_data)
    from m70_ezsocket.m70_giop import M70GIOP
    
    giop_header = M70GIOP.build_giop_header(cnc)
    request_header = M70GIOP.build_request_header(cnc, len(M70GIOP.OP_GET_DATA) + 1)
    
    packet = bytearray()
    op_field = bytearray(16)
    op_bytes = M70GIOP.OP_GET_DATA + b'\x00'
    op_field[:len(op_bytes)] = op_bytes
    packet.extend(op_field)
    
    packet.extend(struct.pack('<I', 0))      # principal
    packet.extend(struct.pack('<I', 2))      # section
    packet.extend(struct.pack('<I', 100))    # sub_section
    packet.extend(struct.pack('<I', 0))      # system_no
    packet.extend(struct.pack('<I', 1))      # axis_flag = 1 (from Wireshark)
    packet.extend(struct.pack('<I', 0))      # u2
    packet.extend(struct.pack('<I', M70DataType.T_CHAR))
    
    # Build full packet
    data_length = len(request_header) + len(packet)
    full_packet = bytearray(giop_header)
    struct.pack_into('<I', full_packet, 8, data_length)
    full_packet.extend(request_header)
    full_packet.extend(packet)
    
    # Send request
    M70Socket.send_data(cnc._socket_obj, bytes(full_packet))
    
    # Receive GIOP reply header
    error_code, remaining_length = M70GIOP.receive_response(cnc)
    print(f"Reply status: {error_code}, remaining data: {remaining_length} bytes")
    
    if remaining_length > 0:
        # Receive response header (12 bytes)
        header = M70Socket.recv_data(cnc._socket_obj, 12)
        if header and len(header) >= 12:
            u1, resp_data_type, data_length = struct.unpack('<III', header)
            print(f"Response header:")
            print(f"  u1 = {u1} (0x{u1:08X})")
            print(f"  resp_data_type = {resp_data_type}")
            print(f"  data_length = {data_length} bytes")
            
            if data_length > 0:
                # Receive actual data
                data_bytes = M70Socket.recv_data(cnc._socket_obj, data_length)
                print(f"\nRaw data ({len(data_bytes)} bytes):")
                print(f"  Hex: {data_bytes.hex()}")
                
                # Try to parse as different types
                if len(data_bytes) >= 1:
                    print(f"  As BYTE: {data_bytes[0]} (0x{data_bytes[0]:02X})")
                    print(f"  → If this is NC unit number, drive would be: M{data_bytes[0]:02X}:")
                
                if len(data_bytes) >= 2:
                    val = struct.unpack('<H', data_bytes[0:2])[0]
                    print(f"  As USHORT: {val} (0x{val:04X})")
                
                if len(data_bytes) >= 4:
                    val = struct.unpack('<I', data_bytes[0:4])[0]
                    print(f"  As UINT32: {val} (0x{val:08X})")
                
                return data_bytes
    
    return None


def test_hypothesis():
    """Test if GIOP returns unit number that EZCOM formats as drive name"""
    
    cnc = M70Connection(ip="192.168.1.214", port=683, nc_type=M70NCType.MELDAS700M)
    
    print("=" * 70)
    print("Testing Hypothesis: GIOP returns NC unit number, EZCOM formats it")
    print("=" * 70)
    print()
    
    if not cnc.connect():
        print("ERROR: Failed to connect to CNC")
        return
    
    print("✓ Connected to CNC")
    print()
    
    # Test 1: Parse raw response
    print("Test 1: Raw GIOP response parsing")
    print("-" * 70)
    raw_data = parse_raw_response(cnc)
    print()
    
    # Test 2: Check if there are multiple units
    print("Test 2: Check for multiple NC units")
    print("-" * 70)
    print("Trying to read with different system_no values...")
    
    for system_no in range(0, 4):
        ret, data = cnc._mel_get_data(2, 100, system_no, 1, M70DataType.T_CHAR)
        print(f"  system_no={system_no}: ret={ret}, data={data} (0x{data:02X})")
        if ret == 0 and data > 0:
            print(f"    → Possible drive: M{data:02X}:")
    print()
    
    # Test 3: Test subsection 101 (might return count)
    print("Test 3: subsection=101 (might return drive count)")
    print("-" * 70)
    ret, count = cnc._mel_get_data(2, 101, 0, 0, M70DataType.T_CHAR)
    print(f"  subsection=101: ret={ret}, count={count}")
    if ret == 0:
        print(f"  → This might indicate {count} drive(s) available")
    print()
    
    # Test 4: Try to get unit number as different types
    print("Test 4: Read unit number as different data types")
    print("-" * 70)
    for dtype_name, dtype in [("T_CHAR", M70DataType.T_CHAR), 
                               ("T_SHORT", M70DataType.T_SHORT),
                               ("T_LONG", M70DataType.T_LONG)]:
        ret, data = cnc._mel_get_data(2, 100, 0, 1, dtype)
        print(f"  {dtype_name}: ret={ret}, data={data} (0x{data:X})")
        if ret == 0 and data > 0:
            print(f"    → Would format as: M{data:02X}:")
    print()
    
    cnc.disconnect()
    print("✓ Disconnected")
    print()
    
    # Analysis
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()
    print("Hypothesis: EZCOM receives NC unit number from GIOP and formats it")
    print()
    print("Evidence from Wireshark:")
    print("  - Reply param1 = 0x01 (unit number)")
    print("  - Reply param2 = 0x01 (possibly count or flag)")
    print("  - NO string data in GIOP packets")
    print()
    print("EZCOM formatting logic (hypothetical):")
    print('  unit_no = giop_reply.param1;  // 0x01')
    print('  sprintf(drive, "M%02X:\\r\\n", unit_no);  // "M01:\\r\\n"')
    print('  return drive;')
    print()
    print("This explains why:")
    print("  ✓ String is not in GIOP packets")
    print("  ✓ COM API returns formatted string")
    print("  ✓ Different CNC configs might have M01, M02, etc.")
    print()


if __name__ == "__main__":
    try:
        test_hypothesis()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
