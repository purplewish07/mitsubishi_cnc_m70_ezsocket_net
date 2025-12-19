"""
Debug script to compare protocol implementations
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import struct
from m70_ezsocket import M70Connection, M70NCType
from m70_ezsocket.m70_giop import M70GIOP

# Test GIOP header building
conn = M70Connection()
conn.nc_type = M70NCType.MELDAS700M
conn.little_endian = True
conn.request_id = 0x1234

print("=== GIOP Header Test ===")
header = M70GIOP.build_giop_header(conn)
print(f"Header length: {len(header)}")
print(f"Header hex: {header.hex()}")
print(f"Magic: {header[0:4]}")
print(f"Version bytes: {header[4:6].hex()}")
version_value = struct.unpack('<H', header[4:6])[0]
print(f"Version value (little-endian): 0x{version_value:04x}")
print(f"Byte order: {header[6]}")
print(f"Message type: {header[7]}")
print(f"Data length: {struct.unpack('<I', header[8:12])[0]}")

print("\n=== Request Header Test ===")
request = M70GIOP.build_request_header(conn, 0x0D)  # mochaGetData length
print(f"Request length: {len(request)}")
print(f"Request hex: {request.hex()}")
print(f"SC list: {struct.unpack('<I', request[0:4])[0]}")
print(f"Request ID: 0x{struct.unpack('<I', request[4:8])[0]:08x}")
print(f"Expected: {request[8]}")
print(f"Reserved: {request[9:12].hex()}")
print(f"Object key length: {struct.unpack('<I', request[12:16])[0]}")
print(f"Object key: {struct.unpack('<I', request[16:20])[0]}")
print(f"Operation length: {struct.unpack('<I', request[20:24])[0]}")

print("\n=== Expected C version values ===")
print("Version should be: 0x0001 (giop->version = 1)")
print("This represents version 0.1, not 1.0!")
print("In C code: ushort version = 1 means bytes: 01 00 (little-endian)")
