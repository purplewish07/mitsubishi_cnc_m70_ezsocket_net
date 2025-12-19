"""
Compare Python packet with expected C packet format
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import struct
from m70_ezsocket.typedef import M70DataType

# Build the expected packet as C would send it
def build_c_style_packet():
    """Build packet exactly as C version does"""
    packet = bytearray()
    
    # GIOP Header (12 bytes)
    packet.extend(b'GIOP')  # magic
    packet.extend(struct.pack('<H', 0x0001))  # version (little-endian)
    packet.append(0x01)  # byte_order (little-endian)
    packet.append(0x00)  # msg_type (REQUEST)
    packet.extend(struct.pack('<I', 68))  # data_length (will calculate)
    
    # Request Header (24 bytes)
    packet.extend(struct.pack('<I', 0))  # sc_list
    packet.extend(struct.pack('<I', 0x1234))  # request_id (example)
    packet.append(0x01)  # expected
    packet.extend(b'\x00\x00\x00')  # reserved
    packet.extend(struct.pack('<I', 4))  # object_key_length
    packet.extend(struct.pack('<I', 1))  # object_key
    packet.extend(struct.pack('<I', 13))  # operation_length (len("mochaGetData"))
    
    # Data Section (44 bytes)
    op_field = bytearray(16)
    op_bytes = b'mochaGetData\x00'
    op_field[:len(op_bytes)] = op_bytes
    packet.extend(op_field)  # op[16]
    
    packet.extend(struct.pack('<I', 0))  # principal
    packet.extend(struct.pack('<I', 67))  # section (NC version)
    packet.extend(struct.pack('<I', 1))  # sub_section
    packet.extend(struct.pack('<I', 0))  # system_no
    packet.extend(struct.pack('<I', 0))  # axis_no
    packet.extend(struct.pack('<I', 0))  # u2
    packet.extend(struct.pack('<I', 0x10))  # data_type (T_STR)
    
    # Update data_length in header
    data_length = len(packet) - 12  # Everything after GIOP header
    struct.pack_into('<I', packet, 8, data_length)
    
    return packet

# Test
packet = build_c_style_packet()
print(f"Packet size: {len(packet)} bytes")
print(f"Expected size: 80 bytes")
print(f"\nFull packet (hex):")
print(packet.hex())
print(f"\nFormatted breakdown:")
print(f"GIOP Header (12 bytes):")
print(f"  Magic: {packet[0:4].hex()} ({packet[0:4]})")
print(f"  Version: {packet[4:6].hex()} (0x{struct.unpack('<H', packet[4:6])[0]:04x})")
print(f"  Byte Order: {packet[6]:02x} ({'LE' if packet[6] == 1 else 'BE'})")
print(f"  Msg Type: {packet[7]:02x}")
print(f"  Data Length: {struct.unpack('<I', packet[8:12])[0]}")

print(f"\nRequest Header (24 bytes):")
print(f"  SC List: {struct.unpack('<I', packet[12:16])[0]}")
print(f"  Request ID: 0x{struct.unpack('<I', packet[16:20])[0]:08x}")
print(f"  Expected: {packet[20]:02x}")
print(f"  Reserved: {packet[21:24].hex()}")
print(f"  Object Key Len: {struct.unpack('<I', packet[24:28])[0]}")
print(f"  Object Key: {struct.unpack('<I', packet[28:32])[0]}")
print(f"  Operation Len: {struct.unpack('<I', packet[32:36])[0]}")

print(f"\nData Section:")
print(f"  Operation (16 bytes): {packet[36:52].hex()}")
op_str = packet[36:52].rstrip(b'\x00').decode('ascii', errors='ignore')
print(f"    String: '{op_str}'")
print(f"  Principal: {struct.unpack('<I', packet[52:56])[0]}")
print(f"  Section: {struct.unpack('<I', packet[56:60])[0]}")
print(f"  Sub-section: {struct.unpack('<I', packet[60:64])[0]}")
print(f"  System No: {struct.unpack('<I', packet[64:68])[0]}")
print(f"  Axis Flag: {struct.unpack('<I', packet[68:72])[0]}")
print(f"  U2: {struct.unpack('<I', packet[72:76])[0]}")
print(f"  Data Type: 0x{struct.unpack('<I', packet[76:80])[0]:02x}")

print("\n" + "="*60)
print("This is the expected C-style packet.")
print("Compare with what Python sends using debug_packets.py")
print("="*60)
