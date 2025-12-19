import sys
import struct
sys.path.insert(0, '..')
sys.path.insert(0, '.')
from m70_ezsocket import M70Connection, M70Logger, M70LogConfig, M70LogLevel, M70LogTarget
from m70_ezsocket.m70_socket import M70Socket
from m70_ezsocket.m70_giop import M70GIOP

# Enable debug logging
config = M70LogConfig()
config.level = M70LogLevel.DEBUG
config.target = M70LogTarget.CONSOLE
M70Logger.init(config)

conn = M70Connection('192.168.1.206', 683, 6)
if conn.connect():
    print('Connected\n')
    
    OP_GET_PROG_BLOCK = b"mochaGetCurrentPrgBlockFirst"
    
    # Build request header
    giop_header = M70GIOP.build_giop_header(conn)
    request_header = M70GIOP.build_request_header(conn, len(OP_GET_PROG_BLOCK) + 1)
    
    # Build data packet
    packet = bytearray()
    op_field = bytearray(32)
    op_bytes = OP_GET_PROG_BLOCK + b'\x00'
    op_field[:len(op_bytes)] = op_bytes
    packet.extend(op_field)
    
    system_no = 1
    row_count = 10
    
    packet.extend(struct.pack('<I', 0))  # principal
    packet.extend(struct.pack('<I', system_no))  # system_no (uint32)
    packet.extend(struct.pack('<I', row_count))  # row_count (uint32)
    
    # Update GIOP header
    data_length = len(request_header) + len(packet)
    full_packet = bytearray(giop_header)
    struct.pack_into('<I', full_packet, 8, data_length)
    full_packet.extend(request_header)
    full_packet.extend(packet)
    
    print(f"Sending packet ({len(full_packet)} bytes):")
    print(full_packet.hex(' '))
    print()
    
    # Send request
    if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
        print("Send failed")
    else:
        print("Send successful, waiting for response...\n")
        
        # Receive GIOP header
        giop_response = M70Socket.recv_data(conn._socket_obj, 12)
        if giop_response:
            print(f"GIOP response header: {giop_response.hex(' ')}")
            magic, version, byte_order, msg_type, msg_size = struct.unpack('<4sHBBI', giop_response)
            print(f"  Magic: {magic}")
            print(f"  Version: 0x{version:04x}")
            print(f"  Byte order: {byte_order}")
            print(f"  Message type: {msg_type} ({'Reply' if msg_type == 1 else 'Request' if msg_type == 0 else 'Unknown'})")
            print(f"  Message size: {msg_size}")
            print()
            
            if msg_size > 0:
                # Read message body
                body = M70Socket.recv_data(conn._socket_obj, msg_size)
                if body:
                    print(f"Message body ({len(body)} bytes):")
                    print(body.hex(' '))
                    print()
                    
                    # Parse reply header
                    if len(body) >= 24:
                        reply_header = body[:24]
                        print(f"Reply header: {reply_header.hex(' ')}")
                        service_context, request_id, reply_status = struct.unpack('<QII', reply_header[:16])
                        print(f"  Service context: {service_context}")
                        print(f"  Request ID: {request_id}")
                        print(f"  Reply status: {reply_status} ({'OK' if reply_status == 0 else 'ERROR'})")
                        
                        if reply_status != 0:
                            # Error response
                            if len(body) >= 28:
                                error_code = struct.unpack('<I', body[24:28])[0]
                                print(f"  Error code: {error_code}")
                        else:
                            # Success - parse data
                            remaining_body = body[24:]
                            if len(remaining_body) >= 12:
                                data_header = remaining_body[:12]
                                u1, resp_data_type, data_len = struct.unpack('<III', data_header)
                                print(f"Data header:")
                                print(f"  u1: {u1}")
                                print(f"  resp_data_type: {resp_data_type}")
                                print(f"  data_len: {data_len}")
                                
                                if data_len > 0 and len(remaining_body) >= 12 + data_len:
                                    data_bytes = remaining_body[12:12+data_len]
                                    print(f"\nData ({data_len} bytes): {data_bytes[:64].hex(' ')}...")
                                    
                                    # Parse prog_block structure
                                    if len(data_bytes) >= 16:
                                        current_block, current_row, u1_field, block_length = struct.unpack('<iiii', data_bytes[0:16])
                                        print(f"\nProg block structure:")
                                        print(f"  current_block: {current_block}")
                                        print(f"  current_row: {current_row}")
                                        print(f"  u1: {u1_field}")
                                        print(f"  block_length: {block_length}")
                                        
                                        if block_length > 0:
                                            text = data_bytes[16:16+min(block_length, 512)]
                                            print(f"  text: {text.decode('utf-8', errors='ignore').rstrip(chr(0))}")
    
    conn.disconnect()
