"""
Test by building packet EXACTLY as C struct would
"""
import socket
import struct
import random

def build_exact_c_packet():
    """Build packet exactly matching C struct layout"""
    # sizeof(get_data_pack) = 80
    packet = bytearray(80)
    pos = 0
    
    # giop_header (12 bytes)
    packet[pos:pos+4] = b'GIOP'
    pos += 4
    struct.pack_into('<H', packet, pos, 0x0001)  # version
    pos += 2
    packet[pos] = 0x01  # byte_order
    pos += 1
    packet[pos] = 0x00  # msg_type
    pos += 1
    struct.pack_into('<I', packet, pos, 68)  # data_length
    pos += 4
    
    # request_pack_header (24 bytes)
    struct.pack_into('<I', packet, pos, 0)  # sc_list
    pos += 4
    struct.pack_into('<I', packet, pos, random.randint(0, 0xFFFF))  # request_id
    pos += 4
    packet[pos] = 0x01  # expected
    pos += 1
    packet[pos:pos+3] = b'\x00\x00\x00'  # reserved
    pos += 3
    struct.pack_into('<I', packet, pos, 4)  # object_key_length
    pos += 4
    struct.pack_into('<I', packet, pos, 1)  # object_key
    pos += 4
    struct.pack_into('<I', packet, pos, 13)  # operation_length
    pos += 4
    
    # char op[16]
    op_bytes = b'mochaGetData\x00'
    packet[pos:pos+len(op_bytes)] = op_bytes
    # Remaining bytes already zero
    pos += 16
    
    # uint32 principal
    struct.pack_into('<I', packet, pos, 0)
    pos += 4
    
    # uint32 section
    struct.pack_into('<I', packet, pos, 67)
    pos += 4
    
    # uint32 sub_section
    struct.pack_into('<I', packet, pos, 1)
    pos += 4
    
    # uint32 system_no
    struct.pack_into('<I', packet, pos, 0)
    pos += 4
    
    # uint32 axis_no
    struct.pack_into('<I', packet, pos, 0)
    pos += 4
    
    # uint32 u2
    struct.pack_into('<I', packet, pos, 0)
    pos += 4
    
    # uint32 data_type
    struct.pack_into('<I', packet, pos, 0x10)  # T_STR
    pos += 4
    
    assert pos == 80, f"Packet size mismatch: {pos} != 80"
    return bytes(packet)

# Connect and send
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)

try:
    print("Connecting to 192.168.1.206:683...")
    sock.connect(("192.168.1.206", 683))
    print("Connected!")
    
    packet = build_exact_c_packet()
    print(f"\nSending {len(packet)} bytes...")
    print(f"Hex: {packet.hex()}")
    
    sock.sendall(packet)
    print("Sent!")
    
    # Receive GIOP header
    print("\nReceiving response...")
    giop_header = sock.recv(12)
    print(f"GIOP Header: {giop_header.hex()}")
    
    magic = giop_header[0:4]
    data_length = struct.unpack('<I', giop_header[8:12])[0]
    print(f"Magic: {magic}, Data Length: {data_length}")
    
    # Receive response header
    response_header = sock.recv(12)
    print(f"Response Header: {response_header.hex()}")
    
    is_error = struct.unpack('<I', response_header[8:12])[0]
    print(f"Is Error: {is_error}")
    
    if is_error != 0:
        print("ERROR RESPONSE!")
        remaining = data_length - 12
        if remaining > 0:
            error_data = sock.recv(remaining)
            print(f"Error Data ({len(error_data)} bytes): {error_data.hex()}")
            if len(error_data) >= 15:
                exc_len = struct.unpack('<I', error_data[0:4])[0]
                print(f"Exception Length: {exc_len}")
                if exc_len > 0 and len(error_data) >= 4 + exc_len:
                    exc_str = error_data[4:4+exc_len]
                    print(f"Exception: {exc_str}")
                if len(error_data) >= 4 + exc_len + 11:
                    error_code = struct.unpack('<I', error_data[4+exc_len+3:4+exc_len+7])[0]
                    print(f"Error Code: 0x{error_code:08x}")
    else:
        print("SUCCESS!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    sock.close()
    print("\nDisconnected")
