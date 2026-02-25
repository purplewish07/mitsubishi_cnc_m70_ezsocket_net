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
        # GIOP header: magic(4) + version(2) + byte_order(1) + msg_type(1) + data_length(4) = 12 bytes
        # C struct: char[4] + ushort + byte + byte + uint32
        magic = b'GIOP'
        # C code: giop->version = 1 (ushort), stored as 0x0001 in little-endian = 01 00
        version = struct.pack('<H', 1)  # ushort = 2 bytes
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
    
    @staticmethod
    def mel_fs_read_file(conn: M70Connection, fd: int, need_read_size: int) -> Tuple[int, int, Optional[bytes]]:
        """
        Read file from CNC file system
        Args:
            conn: M70Connection object
            fd: File descriptor/handle
            need_read_size: Number of bytes to read
        Returns: (error_code, actual_read_size, file_data)
        Corresponds to C function: melFsReadFile
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1, 0, None
        
        if need_read_size == 0:
            return 1, 0, None
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_read_file = "mochaFSReadFile" (16 chars including null = 0x10)
            request_header = M70GIOP.build_request_header(conn, 0x10)
            
            # Build data packet - op field is 16 bytes
            packet = bytearray()
            op_field = bytearray(16)
            op_bytes = M70GIOP.OP_FS_READ_FILE + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', fd))  # file_handle
            packet.extend(struct.pack('<I', need_read_size))  # file_size
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1, 0, None
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            if error_code != 0:
                return error_code, 0, None
            
            # Receive return value and read_size
            actual_read_size = 0
            file_data = None
            
            if remaining_length >= 4:
                ret_data = M70Socket.recv_data(conn._socket_obj, 4)
                remaining_length -= 4
            
            if remaining_length >= 4:
                read_size_data = M70Socket.recv_data(conn._socket_obj, 4)
                actual_read_size = struct.unpack('<I', read_size_data)[0]
                remaining_length -= 4
            
            # Read file data
            if actual_read_size > 0 and remaining_length > 0:
                bytes_to_read = min(actual_read_size, remaining_length)
                file_data = M70Socket.recv_data(conn._socket_obj, bytes_to_read)
                remaining_length -= bytes_to_read
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return 0, actual_read_size, file_data
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_read_file: %s", str(e))
            return 1, 0, None
    
    @staticmethod
    def mel_fs_stat_file(conn: M70Connection, filename: str) -> Tuple[int, Optional[dict]]:
        """
        Get file status/information
        Args:
            conn: M70Connection object
            filename: File path on CNC
        Returns: (error_code, file_stat_dict)
            file_stat_dict contains: mode, file_size, year, month, day, hour, minute, second
        Corresponds to C function: melFSStatFile
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1, None
        
        if not filename or len(filename) == 0:
            return 1, None
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_stat_file = "mochaFSStatFile" (16 chars including null = 0x10)
            request_header = M70GIOP.build_request_header(conn, 0x10)
            
            # Build data packet - op field is 16 bytes
            packet = bytearray()
            op_field = bytearray(16)
            op_bytes = M70GIOP.OP_FS_STAT_FILE + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            filename_bytes = filename.encode('ascii')
            filename_len = len(filename_bytes)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', filename_len))  # file_name_size
            packet.extend(filename_bytes)  # file_name
            
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
            
            # Receive file stat data
            # Response format: header (u1:4, data_length:4, reserved:8) + FileStat structure
            # FileStat structure: mode(4) + reserved1(8) + file_size(4) + reserved2(24) + time_fields(24) = 64 bytes
            file_stat = None
            
            if remaining_length >= 16:  # header size
                # Read response header
                header_data = M70Socket.recv_data(conn._socket_obj, 16)
                u1, data_length = struct.unpack('<II', header_data[:8])
                remaining_length -= 16
                
                # Read FileStat structure (64 bytes total)
                # mode(4) + reserved1(8) + file_size(4) + reserved2(24) + year(4) + month(4) + day(4) + hour(4) + minute(4) + second(4)
                if remaining_length >= 64 and data_length >= 64:
                    stat_data = M70Socket.recv_data(conn._socket_obj, 64)
                    
                    # Unpack: mode, skip 8 bytes, file_size, skip 24 bytes, then 6 time fields
                    mode = struct.unpack('<III', stat_data[0:12])[0]
                    # reserved1 at offset 4-11 (8 bytes)
                    file_size = struct.unpack('<I', stat_data[12:16])[0]
                    # reserved2 at offset 16-39 (24 bytes)
                    year, month, day, hour, minute, second = struct.unpack('<6I', stat_data[40:64])
                    # print(f"stat_data Raw: {stat_data.hex()}")
                    # print(f"Parsed time: year={year}, month={month}, day={day}, hour={hour}, minute={minute}, second={second}")
                    
                    file_stat = {
                        'mode': mode,
                        'file_size': file_size,
                        'year': 1950 + year,  # Base year is 1950
                        'month': month,
                        'day': day,
                        'hour': hour,
                        'minute': minute,
                        'second': second
                    }
                    remaining_length -= 64
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return 0, file_stat
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_stat_file: %s", str(e))
            return 1, None
    
    @staticmethod
    def mel_fs_read_directory(conn: M70Connection, fd: int) -> Tuple[int, Optional[str]]:
        """
        Read directory entry
        Args:
            conn: M70Connection object
            fd: Directory descriptor/handle
        Returns: (error_code, directory_name)
        Corresponds to C function: melFsReadDirectory
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1, None
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_read_dir = "mochaFSReadDirectory" (24 chars including null = 0x15)
            request_header = M70GIOP.build_request_header(conn, 0x15)
            
            # Build data packet - op field is 24 bytes
            packet = bytearray()
            op_field = bytearray(24)
            op_bytes = M70GIOP.OP_FS_READ_DIR + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', fd))  # file_handle
            
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
            
            # Receive directory data
            dirname = None
            
            # First ret value (4 bytes)
            if remaining_length >= 4:
                ret_data = M70Socket.recv_data(conn._socket_obj, 4)
                remaining_length -= 4
            
            # datasize (4 bytes)
            if remaining_length >= 4:
                datasize_data = M70Socket.recv_data(conn._socket_obj, 4)
                datasize = struct.unpack('<I', datasize_data)[0]
                remaining_length -= 4
                
                if datasize > 0:
                    # Second ret value (4 bytes)
                    if remaining_length >= 4:
                        ret_data2 = M70Socket.recv_data(conn._socket_obj, 4)
                        remaining_length -= 4
                    
                    # size (4 bytes)
                    if remaining_length >= 4:
                        size_data = M70Socket.recv_data(conn._socket_obj, 4)
                        size = struct.unpack('<I', size_data)[0]
                        remaining_length -= 4
                        
                        # Read directory name
                        if size > 0 and remaining_length >= size:
                            dirname_data = M70Socket.recv_data(conn._socket_obj, size)
                            # C code sets last byte to newline: dirname[size - 1] = '\n'
                            dirname = dirname_data.decode('ascii', errors='ignore').rstrip('\x00')
                            remaining_length -= size
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return 0, dirname
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_read_directory: %s", str(e))
            return 1, None
    
    @staticmethod
    def mel_fs_open_file(conn: M70Connection, filename: str, mode: int) -> Tuple[int, int]:
        """
        Open file on CNC file system
        Args:
            conn: M70Connection object
            filename: File path on CNC
            mode: File open mode (0=read, 1=write, 2=read/write)
        Returns: (error_code, file_descriptor)
        Corresponds to C function: melFsOpenFile
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1, 0
        
        if not filename or len(filename) == 0:
            return 1, 0
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_open_file = "mochaFSOpenFile" (16 chars including null = 0x10)
            request_header = M70GIOP.build_request_header(conn, 0x10)
            
            # Build data packet - op field is 16 bytes
            packet = bytearray()
            op_field = bytearray(16)
            op_bytes = M70GIOP.OP_FS_OPEN_FILE + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            filename_bytes = filename.encode('ascii')
            filename_len = len(filename_bytes)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', 0))  # mode (always 0 in C code)
            packet.extend(struct.pack('<I', mode))  # flag
            packet.extend(struct.pack('<I', filename_len))  # file_name_size
            packet.extend(filename_bytes)  # file_name
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1, 0
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            if error_code != 0:
                return error_code, 0
            
            # Receive return value and file descriptor
            fd = 0
            if remaining_length >= 4:
                ret_data = M70Socket.recv_data(conn._socket_obj, 4)
                remaining_length -= 4
            
            if remaining_length >= 4:
                fd_data = M70Socket.recv_data(conn._socket_obj, 4)
                fd = struct.unpack('<I', fd_data)[0]
                remaining_length -= 4
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return 0, fd
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_open_file: %s", str(e))
            return 1, 0
    
    @staticmethod
    def mel_fs_close_file(conn: M70Connection, fd: int) -> int:
        """
        Close file on CNC file system
        Args:
            conn: M70Connection object
            fd: File descriptor/handle
        Returns: error_code
        Corresponds to C function: melFsCloseFile
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_close_file = "mochaFSCloseFile" (17 chars including null = 0x11)
            request_header = M70GIOP.build_request_header(conn, 0x11)
            
            # Build data packet - op field is 17 bytes + 3 reserved bytes = 20 bytes
            packet = bytearray()
            op_field = bytearray(17)
            op_bytes = M70GIOP.OP_FS_CLOSE_FILE + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            packet.extend(b'\x00\x00\x00')  # reserved (3 bytes)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', fd))  # file_handle
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return error_code
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_close_file: %s", str(e))
            return 1
    
    @staticmethod
    def mel_fs_open_directory(conn: M70Connection, dirpath: str) -> Tuple[int, int]:
        """
        Open directory on CNC file system
        Args:
            conn: M70Connection object
            dirpath: Directory path on CNC
        Returns: (error_code, directory_descriptor)
        Corresponds to C function: melFsOpenDirectory
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1, 0
        
        if not dirpath or len(dirpath) == 0:
            return 1, 0
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_open_dir = "mochaFSOpenDirectory" (24 chars including null = 0x15)
            request_header = M70GIOP.build_request_header(conn, 0x15)
            
            # Build data packet - op field is 24 bytes
            packet = bytearray()
            op_field = bytearray(24)
            op_bytes = M70GIOP.OP_FS_OPEN_DIR + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            dirpath_bytes = dirpath.encode('ascii')
            dirpath_len = len(dirpath_bytes)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', dirpath_len))  # path_name_size
            packet.extend(dirpath_bytes)  # path_name
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1, 0
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            if error_code != 0:
                return error_code, 0
            
            # Receive return value and directory descriptor
            fd = 0
            if remaining_length >= 4:
                ret_data = M70Socket.recv_data(conn._socket_obj, 4)
                remaining_length -= 4
            
            if remaining_length >= 4:
                fd_data = M70Socket.recv_data(conn._socket_obj, 4)
                fd = struct.unpack('<I', fd_data)[0]
                remaining_length -= 4
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return 0, fd
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_open_directory: %s", str(e))
            return 1, 0
    
    @staticmethod
    def mel_fs_close_directory(conn: M70Connection, fd: int) -> int:
        """
        Close directory on CNC file system
        Args:
            conn: M70Connection object
            fd: Directory descriptor/handle
        Returns: error_code
        Corresponds to C function: melFsCloseDirectory
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_close_dir = "mochaFSCloseDirectory" (24 chars including null, op_length = 0x16)
            request_header = M70GIOP.build_request_header(conn, 0x16)
            
            # Build data packet - op field is 24 bytes
            packet = bytearray()
            op_field = bytearray(24)
            op_bytes = M70GIOP.OP_FS_CLOSE_DIR + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', fd))  # file_handle
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return error_code
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_close_directory: %s", str(e))
            return 1

    @staticmethod
    def mel_fs_create_file(conn: 'M70Connection', filename: str, mode: int) -> Tuple[int, int]:
        """
        Create a new file on CNC file system
        Args:
            conn: M70Connection object
            filename: File path on CNC
            mode: File access mode (0=read, 1=write, 2=read/write)
        Returns: (error_code, fd)
            fd is the file descriptor/handle
        Corresponds to C function: melFsCreateFile
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1, 0
        
        if not filename or len(filename) == 0:
            return 1, 0
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_create_file = "mochaFSCreateFile" (18 chars including null = 0x12)
            request_header = M70GIOP.build_request_header(conn, 0x12)
            
            # Build data packet
            packet = bytearray()
            
            # op field is 18 bytes (0x12)
            op_field = bytearray(18)
            op_bytes = M70GIOP.OP_FS_CREATE_FILE + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            # reserved (2 bytes)
            packet.extend(b'\x00\x00')
            
            filename_bytes = filename.encode('ascii')
            filename_len = len(filename_bytes)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', mode))  # mode
            packet.extend(struct.pack('<I', filename_len))  # file_name_size
            packet.extend(filename_bytes)  # file_name
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1, 0
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            if error_code != 0:
                return error_code, 0
            
            # Receive file descriptor
            # Response format: ret(4) + fd(4)
            fd = 0
            if remaining_length >= 8:
                ret_data = M70Socket.recv_data(conn._socket_obj, 4)
                fd_data = M70Socket.recv_data(conn._socket_obj, 4)
                fd = struct.unpack('<I', fd_data)[0]
                remaining_length -= 8
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return 0, fd
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_create_file: %s", str(e))
            return 1, 0

    @staticmethod
    def mel_fs_write_file(conn: 'M70Connection', fd: int, file_data: bytes, write_size: int) -> Tuple[int, int]:
        """
        Write data to a file
        Args:
            conn: M70Connection object
            fd: File descriptor/handle
            file_data: Data to write
            write_size: Number of bytes to write
        Returns: (error_code, actual_written_size)
        Corresponds to C function: melFsWriteFile
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1, 0
        
        if not file_data or write_size <= 0:
            return 1, 0
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_write_file = "mochaFSWriteFile" (17 chars, padded to 20 = 0x14, but header uses 0x11)
            request_header = M70GIOP.build_request_header(conn, 0x11)
            
            # Build data packet
            packet = bytearray()
            
            # op field is 20 bytes
            op_field = bytearray(20)
            op_bytes = M70GIOP.OP_FS_WRITE_FILE + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', fd))  # file_handle
            packet.extend(struct.pack('<I', write_size))  # file_size
            packet.extend(file_data[:write_size])  # file_data
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1, 0
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            if error_code != 0:
                return error_code, 0
            
            # Receive actual written size
            # Response format: ret(4) + real_write_size(4)
            actual_written = 0
            if remaining_length >= 8:
                ret_data = M70Socket.recv_data(conn._socket_obj, 4)
                size_data = M70Socket.recv_data(conn._socket_obj, 4)
                actual_written = struct.unpack('<I', size_data)[0]
                remaining_length -= 8
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return 0, actual_written
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_write_file: %s", str(e))
            return 1, 0

    @staticmethod
    def mel_fs_remove_file(conn: 'M70Connection', filename: str) -> int:
        """
        Remove/delete a file from CNC file system
        Args:
            conn: M70Connection object
            filename: File path on CNC to remove
        Returns: error_code (0=success, non-zero=error)
        Corresponds to C function: melRemoveFile
        """
        if not M70GIOP.check_connection_valid(conn):
            return 1
        
        if not filename or len(filename) == 0:
            return 1
        
        try:
            # Build request header
            giop_header = M70GIOP.build_giop_header(conn)
            # op_command_fs_remove_file = "mochaFSRemoveFile" (18 chars including null = 0x12)
            request_header = M70GIOP.build_request_header(conn, 0x12)
            
            # Build data packet
            packet = bytearray()
            
            # op field is 18 bytes
            op_field = bytearray(18)
            op_bytes = M70GIOP.OP_FS_REMOVE_FILE + b'\x00'
            op_field[:len(op_bytes)] = op_bytes
            packet.extend(op_field)
            
            # reserved (2 bytes)
            packet.extend(b'\x00\x00')
            
            filename_bytes = filename.encode('ascii')
            filename_len = len(filename_bytes)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', filename_len))  # fileLen
            packet.extend(filename_bytes)  # file_name
            
            # Update GIOP header
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(conn._socket_obj, bytes(full_packet)) < 0:
                return 1
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(conn)
            
            # Discard remaining data
            M70GIOP.receive_remaining_data(conn, remaining_length)
            
            return error_code
            
        except Exception as e:
            M70Logger.error("Error in mel_fs_remove_file: %s", str(e))
            return 1

