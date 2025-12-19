import sys
import struct
sys.path.insert(0, '..')
sys.path.insert(0, '.')
from m70_ezsocket import M70Connection
from m70_ezsocket.m70_giop import M70GIOP

# Create connection but don't actually send
conn = M70Connection('192.168.1.206', 683, 6)

# Build prog_block packet manually
OP_GET_PROG_BLOCK = b"mochaGetCurrentPrgBlockFirst"

giop_header = M70GIOP.build_giop_header(conn)
request_header = M70GIOP.build_request_header(conn, len(OP_GET_PROG_BLOCK) + 1)

# Build data packet - op field must be 32 bytes
packet = bytearray()
op_field = bytearray(32)
op_bytes = OP_GET_PROG_BLOCK + b'\x00'
op_field[:len(op_bytes)] = op_bytes
packet.extend(op_field)

system_no = 1
row_count = 10

packet.extend(struct.pack('<I', 0))  # principal
packet.extend(struct.pack('<I', system_no))  # system_no (unsigned)
packet.extend(struct.pack('<I', row_count))  # row_count (unsigned)

# Update GIOP header
data_length = len(request_header) + len(packet)
full_packet = bytearray(giop_header)
struct.pack_into('<I', full_packet, 8, data_length)
full_packet.extend(request_header)
full_packet.extend(packet)

print(f"Total packet length: {len(full_packet)}")
print(f"GIOP header (12 bytes): {giop_header.hex(' ')}")
print(f"Request header ({len(request_header)} bytes): {request_header.hex(' ')}")
print(f"Data packet ({len(packet)} bytes):")
print(f"  op field (32 bytes): {packet[:32].hex(' ')}")
print(f"  principal (4 bytes): {packet[32:36].hex(' ')}")
print(f"  system_no (4 bytes): {packet[36:40].hex(' ')}")
print(f"  row_count (4 bytes): {packet[40:44].hex(' ')}")
print(f"\nFull packet hex:\n{full_packet.hex(' ')}")

# Calculate expected sizes
print(f"\nExpected structure sizes:")
print(f"  giop_header: 12 bytes")
print(f"  request_pack_header: {len(request_header)} bytes")
print(f"  op[32]: 32 bytes")
print(f"  principal: 4 bytes")
print(f"  system_no: 4 bytes")
print(f"  row_count: 4 bytes")
print(f"  Total data: {len(request_header) + len(packet)} bytes")
print(f"  Total packet: {12 + len(request_header) + len(packet)} bytes")
