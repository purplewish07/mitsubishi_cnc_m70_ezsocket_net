#!/usr/bin/env python3
"""
Parse the complete GIOP reply structure for File_GetDriveInformation
Based on Wireshark packet 1955 analysis
"""

import sys
import os
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from m70_ezsocket import M70Connection, M70NCType
from m70_ezsocket.typedef import M70DataType
from m70_ezsocket.m70_socket import M70Socket
from m70_ezsocket.m70_giop import M70GIOP


def parse_complete_reply(cnc):
    """
    Parse COMPLETE GIOP reply including ALL fields
    Don't use the normal parsing - capture everything
    """
    print("Sending mochaGetData(2, 100, 0, 1) request...")
    print()
    
    # Build and send request
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
    packet.extend(struct.pack('<I', 1))      # axis_flag
    packet.extend(struct.pack('<I', 0))      # u2
    packet.extend(struct.pack('<I', M70DataType.T_CHAR))
    
    data_length = len(request_header) + len(packet)
    full_packet = bytearray(giop_header)
    struct.pack_into('<I', full_packet, 8, data_length)
    full_packet.extend(request_header)
    full_packet.extend(packet)
    
    M70Socket.send_data(cnc._socket_obj, bytes(full_packet))
    
    # Receive GIOP Reply Header (12 bytes header)
    giop_reply = M70Socket.recv_data(cnc._socket_obj, 12)
    if not giop_reply or len(giop_reply) < 12:
        print("ERROR: Failed to receive GIOP reply header")
        return
    
    magic = giop_reply[0:4]
    version = giop_reply[4:6]
    byte_order = giop_reply[6]
    msg_type = giop_reply[7]
    msg_size = struct.unpack('<I', giop_reply[8:12])[0]
    
    print("=" * 70)
    print("GIOP Reply Header:")
    print("=" * 70)
    print(f"Magic: {magic.decode('ascii')}")
    print(f"Version: {version[0]}.{version[1]}")
    print(f"Byte Order: {byte_order} (0=Big Endian, 1=Little Endian)")
    print(f"Message Type: {msg_type} (1=Reply)")
    print(f"Message Size: {msg_size} bytes")
    print()
    
    # Receive Reply Header (from message body)
    reply_header = M70Socket.recv_data(cnc._socket_obj, 12)
    if not reply_header or len(reply_header) < 12:
        print("ERROR: Failed to receive reply header")
        return
    
    service_ctx_len = struct.unpack('<I', reply_header[0:4])[0]
    request_id = struct.unpack('<I', reply_header[4:8])[0]
    reply_status = struct.unpack('<I', reply_header[8:12])[0]
    
    print("=" * 70)
    print("Reply Header:")
    print("=" * 70)
    print(f"Service Context Length: {service_ctx_len}")
    print(f"Request ID: {request_id} (0x{request_id:08X})")
    print(f"Reply Status: {reply_status} (0=NO_EXCEPTION)")
    print()
    
    # Receive remaining data
    remaining = msg_size - 12  # Already read 12 bytes of reply header
    print(f"Remaining data to read: {remaining} bytes")
    print()
    
    if remaining > 0:
        data = M70Socket.recv_data(cnc._socket_obj, remaining)
        
        print("=" * 70)
        print("Reply Body (Complete Raw Data):")
        print("=" * 70)
        print(f"Length: {len(data)} bytes")
        print(f"Hex: {data.hex()}")
        print()
        
        # Parse as int32 values
        print("Parsing as sequence of int32 values:")
        offset = 0
        index = 0
        while offset + 4 <= len(data):
            val = struct.unpack('<I', data[offset:offset+4])[0]
            print(f"  int32[{index}] @ offset {offset}: {val} (0x{val:08X})")
            offset += 4
            index += 1
        
        # Show remaining bytes
        if offset < len(data):
            print(f"  Remaining bytes: {data[offset:].hex()}")
        print()
        
        # Try to interpret based on standard mel_get_data response
        print("=" * 70)
        print("Standard Response Structure Interpretation:")
        print("=" * 70)
        
        if len(data) >= 12:
            # Standard response: u1 (4), data_type (4), data_length (4), [data...]
            u1 = struct.unpack('<I', data[0:4])[0]
            data_type = struct.unpack('<I', data[4:8])[0]
            data_len = struct.unpack('<I', data[8:12])[0]
            
            print(f"u1 (unknown field): {u1} (0x{u1:08X})")
            print(f"data_type: {data_type}")
            print(f"data_length: {data_len} bytes")
            print()
            
            if data_len > 0 and len(data) >= 12 + data_len:
                actual_data = data[12:12+data_len]
                print(f"Actual data ({data_len} bytes): {actual_data.hex()}")
                
                if data_len == 1:
                    print(f"  As BYTE: {actual_data[0]} (0x{actual_data[0]:02X})")
                    print(f"  → If drive count: {actual_data[0]} drive(s)")
                    print(f"  → If unit number: M{actual_data[0]:02X}:")
                elif data_len == 4:
                    val = struct.unpack('<I', actual_data)[0]
                    print(f"  As UINT32: {val} (0x{val:08X})")
        
        return data
    
    return None


def main():
    cnc = M70Connection(ip="192.168.1.214", port=683, nc_type=M70NCType.MELDAS700M)
    
    print("=" * 70)
    print("Complete GIOP Reply Parser for File_GetDriveInformation")
    print("=" * 70)
    print()
    
    if not cnc.connect():
        print("ERROR: Failed to connect")
        return
    
    print("✓ Connected to CNC")
    print()
    
    reply_data = parse_complete_reply(cnc)
    
    cnc.disconnect()
    print()
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print()
    print("From Wireshark packet 1955:")
    print("  Reply body: 00 00 00 00  01 00 00 00  01 00 00 00  00")
    print()
    print("Interpretation:")
    print("  [0-3]:  return_code = 0 (success)")
    print("  [4-7]:  field1 = 1")
    print("  [8-11]: field2 = 1")
    print("  [12]:   end_marker = 0")
    print()
    print("This is the standard mel_get_data response structure:")
    print("  - u1 (4 bytes)")
    print("  - data_type (4 bytes)")
    print("  - data_length (4 bytes)")
    print("  - data (N bytes)")
    print()
    print("So field1=1 might be the data_type (T_CHAR)")
    print("And field2=1 might be the data_length (1 byte)")
    print()
    print("But where is the actual data byte?")
    print("The response structure suggests there should be 1 more byte after offset 12!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
