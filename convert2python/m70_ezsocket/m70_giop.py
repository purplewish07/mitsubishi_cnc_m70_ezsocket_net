"""
GIOP protocol layer for M70 EZSocket communication
Converted from m70_giop.h and m70_giop.c
"""

import struct
import socket
import random
import sys
from typing import Optional, Tuple, Any
from .typedef import *
from .m70_socket import M70Socket
from .m70_log import M70Logger
from .m70_error import M70ErrorHandler


class GIOPMessageType(IntEnum):
    """GIOP message types"""
    REQUEST = 0
    REPLY = 1
    CANCEL_REQUEST = 2
    LOCATE_REQUEST = 3
    LOCATE_REPLY = 4
    CLOSE_CONNECTION = 5
    MESSAGE_ERROR = 6


class M70GIOP:
    """GIOP protocol handler"""
    
    # GIOP operation commands
    OP_GET_DATA = b"mochaGetData"
    OP_SET_DATA = b"mochaSetData"
    OP_GET_ALARM_MSG = b"mochaGetCurrentAlarmMsgFirst"
    OP_GET_PROG_BLOCK = b"mochaGetCurrentPrgBlockFirst"
    OP_FS_OPEN_FILE = b"mochaFSOpenFile"
    OP_FS_READ_FILE = b"mochaFSReadFile"
    OP_FS_CLOSE_FILE = b"mochaFSCloseFile"
    OP_FS_CREATE_FILE = b"mochaFSCreateFile"
    OP_FS_REMOVE_FILE = b"mochaFSRemoveFile"
    OP_FS_WRITE_FILE = b"mochaFSWriteFile"
    OP_FS_STAT_FILE = b"mochaFSStatFile"
    OP_FS_OPEN_DIR = b"mochaFSOpenDirectory"
    OP_FS_CLOSE_DIR = b"mochaFSCloseDirectory"
    OP_FS_READ_DIR = b"mochaFSReadDirectory"
    OP_CANCEL_MODAL2 = b"mochaCancelModal2"
    
    # Data type sizes
    DATA_TYPE_SIZES = {
        M70DataType.T_CHAR: 1,
        M70DataType.T_SHORT: 2,
        M70DataType.T_LONG: 4,
        M70DataType.T_DLONG: 8,
        M70DataType.T_DOUBLE: 8,
        M70DataType.T_FLOATBIN: 16,
        M70DataType.T_CLCTDATA: 36,
    }
    
    @staticmethod
    def is_little_endian() -> bool:
        """Check if system is little endian"""
        return sys.byteorder == 'little'
    
    @staticmethod
    def get_data_type_length(data_type: M70DataType) -> int:
        """Get the length of a data type"""
        return M70GIOP.DATA_TYPE_SIZES.get(data_type, 1)
    
    @staticmethod
    def build_giop_header(conn: M70Connection) -> bytes:
        """Build GIOP header"""
        # GIOP header: magic(4) + version(2) + byte_order(1) + msg_type(1) + data_length(4)
        magic = b'GIOP'
        # C version sets: giop->version = 1, which means 0x0001 in little-endian (01 00 bytes)
        version = struct.pack('<H', 0x0001)  # Version 0.1 (matches C implementation)
        byte_order = b'\x01' if conn.little_endian else b'\x00'
        msg_type = struct.pack('B', GIOPMessageType.REQUEST)
        data_length = struct.pack('<I', 0)  # Will be updated later
        
        return magic + version + byte_order + msg_type + data_length
    
    @staticmethod
    def build_request_header(conn: M70Connection, op_name_length: int) -> bytes:
        """Build request packet header"""
        sc_list = struct.pack('<I', 0)
        # C version does NOT increment request_id for each request - it stays constant
        request_id = struct.pack('<I', conn.request_id)
        expected = struct.pack('B', 1)
        reserved = b'\x00\x00\x00'
        object_key_length = struct.pack('<I', 4)
        object_key = struct.pack('<I', 1)
        operation_length = struct.pack('<I', op_name_length)
        
        return sc_list + request_id + expected + reserved + object_key_length + object_key + operation_length
    
    @staticmethod
    def connect(ip: str, port: int, nc_type: M70NCType) -> Optional[M70Connection]:
        """Connect to M70 CNC machine"""
        M70Logger.info("Attempting to connect to CNC device: %s:%d, Type: %d", ip, port, nc_type)
        
        if not ip or port <= 0:
            M70ErrorHandler.set_error(M70ErrorCode.FAILED, f"Invalid connection parameters: IP={ip}, Port={port}")
            M70Logger.error("Invalid connection parameters: IP=%s, Port=%d", ip, port)
            return None
        
        # Create connection object
        conn = M70Connection()
        conn.nc_type = nc_type
        conn.little_endian = True
        conn.request_id = random.randint(0, 0xFFFF)
        
        # Open TCP socket
        sock = M70Socket.open_tcp_client_socket(ip, port)
        if sock is None:
            M70ErrorHandler.set_error(M70ErrorCode.SOCKET_FAILED, f"Failed to connect to {ip}:{port}")
            M70Logger.error("Failed to connect to CNC device: %s:%d", ip, port)
            return None
        
        conn.socket = sock.fileno()
        conn.connected = True
        conn._socket_obj = sock  # Store socket object
        
        M70Logger.info("Successfully connected to CNC device: %s:%d", ip, port)
        return conn
    
    @staticmethod
    def disconnect(conn: M70Connection):
        """Disconnect from M70 CNC machine"""
        if conn and hasattr(conn, '_socket_obj') and conn._socket_obj:
            M70Logger.info("Disconnecting from CNC device")
            M70Socket.close_tcp_socket(conn._socket_obj)
            conn.socket = -1
            conn.connected = False
            conn._socket_obj = None
    
    @staticmethod
    def check_connection_valid(conn: M70Connection) -> bool:
        """Check if connection is valid"""
        return conn is not None and conn.connected and hasattr(conn, '_socket_obj') and conn._socket_obj is not None
    
    @staticmethod
    def receive_response(conn: M70Connection) -> Tuple[int, int]:
        """
        Receive response from CNC
        Returns: (error_code, remaining_length)
        """
        if not M70GIOP.check_connection_valid(conn):
            return -1, 0
        
        # Receive GIOP header (12 bytes)
        header_data = M70Socket.recv_data(conn._socket_obj, 12)
        if not header_data or len(header_data) < 12:
            M70Logger.error("Failed to receive GIOP header")
            return -1, 0
        
        # Parse GIOP header
        magic = header_data[0:4]
        version = struct.unpack('<H', header_data[4:6])[0]
        byte_order = header_data[6]
        msg_type = header_data[7]
        data_length = struct.unpack('<I', header_data[8:12])[0]
        
        if magic != b'GIOP':
            M70Logger.error("Invalid GIOP magic number")
            return -1, 0
        
        # Receive response header (12 bytes)
        response_header = M70Socket.recv_data(conn._socket_obj, 12)
        if not response_header or len(response_header) < 12:
            M70Logger.error("Failed to receive response header")
            return -1, 0
        
        sc_list = struct.unpack('<I', response_header[0:4])[0]
        request_id = struct.unpack('<I', response_header[4:8])[0]
        is_error = struct.unpack('<I', response_header[8:12])[0]
        
        remaining_length = data_length - 12
        
        if is_error != 0:
            # Handle error response
            M70Logger.warning("Received error response: error=%d", is_error)
            error_code, bytes_consumed = M70GIOP.receive_error_response(conn, remaining_length)
            remaining_length -= bytes_consumed
            # Consume any remaining bytes
            if remaining_length > 0:
                M70Socket.recv_data(conn._socket_obj, remaining_length)
            return error_code, 0
        
        return 0, remaining_length
    
    @staticmethod
    def receive_error_response(conn: M70Connection, remaining_length: int) -> Tuple[int, int]:
        """Receive error response
        Returns: (error_code, bytes_consumed)
        """
        bytes_consumed = 0
        error_code = -1
        
        # Receive exception length
        if remaining_length >= 4:
            exception_len_data = M70Socket.recv_data(conn._socket_obj, 4)
            if not exception_len_data:
                return -1, bytes_consumed
            exception_len = struct.unpack('<I', exception_len_data)[0]
            bytes_consumed += 4
            remaining_length -= 4
            
            # Receive remaining info (exception string)
            if exception_len > 0 and remaining_length > 0:
                bytes_to_read = min(exception_len, remaining_length)
                exception_data = M70Socket.recv_data(conn._socket_obj, bytes_to_read)
                bytes_consumed += bytes_to_read
                remaining_length -= bytes_to_read
        
        # Receive error code structure (mel_error_code: 3 bytes + 4 bytes + 4 bytes = 11 bytes)
        if remaining_length >= 11:
            error_pack_data = M70Socket.recv_data(conn._socket_obj, 11)
            if error_pack_data and len(error_pack_data) >= 11:
                # Skip first 3 bytes, get error_code (next 4 bytes)
                error_code = struct.unpack('<I', error_pack_data[3:7])[0]
                bytes_consumed += 11
        
        return error_code, bytes_consumed
    
    @staticmethod
    def receive_remaining_data(conn: M70Connection, length: int):
        """Receive and discard remaining data"""
        if length > 0 and M70GIOP.check_connection_valid(conn):
            M70Socket.recv_data(conn._socket_obj, length)
    
    @staticmethod
    def mel_get_current_alarm_msg(conn: M70Connection, system_no: int, msg_count: int, 
                                   msg_type: int) -> Tuple[int, Optional[bytes]]:
        """
        Get current alarm messages
        Returns: (error_code, alarm_data)
        Corresponds to C function: melGetCurrentAlarmMsg
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1, None
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_get_alarm_msg = "mochaGetCurrentAlarmMsgFirst" (29 chars + 1 null = 0x1D)
            request_header = M70GIOP.build_request_header(conn, 0x1D)
            
            # Build data packet - op field must be 32 bytes
            packet = bytearray()
            op_field = bytearray(32)
            op_bytes = M70GIOP.OP_GET_ALARM_MSG + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', system_no))  # system_no (uint32)
            packet.extend(struct.pack('<I', msg_count))  # msg_count (uint32)
            packet.extend(struct.pack('<I', msg_type))  # msg_type (uint32)
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1, None
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            if error_code != 0:
                return error_code, None
            
            # alarm_string response is directly the structure, no data header
            alarm_data = None
            if remaining_length > 0:
                alarm_data = M70Socket.recv_data(conn._socket_obj, remaining_length)
            
            return 0, alarm_data
            
        except Exception as e:
            M70Logger.error("Error in mel_get_current_alarm_msg: %s", str(e))
            return 1, None
    
    @staticmethod
    def mel_get_current_prg_block(conn: M70Connection, system_no: int, 
                                   row_count: int) -> Tuple[int, Optional[bytes]]:
        """
        Get current program block
        Returns: (error_code, prog_block_data)
        Corresponds to C function: melGetCurrentPrgBlock
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1, None
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_get_prog_block = "mochaGetCurrentPrgBlockFirst" (29 chars + 1 null = 0x1D)
            request_header = M70GIOP.build_request_header(conn, 0x1D)
            
            # Build data packet - op field must be 32 bytes
            packet = bytearray()
            op_field = bytearray(32)
            op_bytes = M70GIOP.OP_GET_PROG_BLOCK + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', system_no))  # system_no (uint32)
            packet.extend(struct.pack('<I', row_count))  # row_count (uint32)
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1, None
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            if error_code != 0:
                return error_code, None
            
            # prog_block response is directly the structure, no data header
            prog_block_data = None
            if remaining_length > 0:
                prog_block_data = M70Socket.recv_data(conn._socket_obj, remaining_length)
            
            return 0, prog_block_data
            
        except Exception as e:
            M70Logger.error("Error in mel_get_current_prg_block: %s", str(e))
            return 1, None
