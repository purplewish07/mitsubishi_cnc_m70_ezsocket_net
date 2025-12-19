"""
M70 CNC Connection and API Layer
Main interface for communicating with Mitsubishi CNC M70 machines
Converted from m70_ezsocket.h and m70_ezsocket.c
"""

import struct
from typing import Optional, List, Tuple
from .typedef import *
from .m70_giop import M70GIOP
from .m70_socket import M70Socket
from .m70_log import M70Logger
from .m70_error import M70ErrorHandler, M70Error


class M70Connection:
    """Main connection class for M70 CNC machine"""
    
    def __init__(self, ip: str = "", port: int = 683, nc_type: M70NCType = M70NCType.MELDAS700M):
        self.socket = -1
        self.connected = False
        self.nc_type = nc_type
        self.request_id = 0
        self.little_endian = True
        self._socket_obj = None
        self._ip = ip
        self._port = port
    
    def connect(self) -> bool:
        """Connect to CNC machine"""
        conn_obj = M70GIOP.connect(self._ip, self._port, self.nc_type)
        if conn_obj:
            self.socket = conn_obj.socket
            self.connected = conn_obj.connected
            self.nc_type = conn_obj.nc_type
            self.request_id = conn_obj.request_id
            self.little_endian = conn_obj.little_endian
            self._socket_obj = conn_obj._socket_obj
            return True
        return False
    
    def disconnect(self):
        """Disconnect from CNC machine"""
        M70GIOP.disconnect(self)
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return M70GIOP.check_connection_valid(self)
    
    # ==================== Read Status Methods ====================
    
    def read_status(self, system_no: int = 1) -> Tuple[M70ErrorCode, M70DeviceStatus, M70RunMode, M70RunStatus]:
        """
        Read CNC status
        Returns: (error_code, device_status, run_mode, run_status)
        """
        M70Logger.debug("Reading CNC status, System No: %d", system_no)
        
        if not self.is_connected():
            M70ErrorHandler.set_error(M70ErrorCode.FAILED, "Invalid connection")
            M70Logger.error("Failed to read CNC status: Invalid connection")
            return M70ErrorCode.FAILED, M70DeviceStatus.OFFLINE, M70RunMode.MEM, M70RunStatus.RST
        
        status = M70DeviceStatus.OFFLINE
        mode = M70RunMode.MEM
        run_status = M70RunStatus.RST
        
        # Read run mode
        ret, temp_mode = self._mel_get_data(35, 11, system_no, 0, M70DataType.T_SHORT)
        if ret == 0:
            mode = M70RunMode(temp_mode)
            status = M70DeviceStatus.IDLE
            M70Logger.debug("CNC running mode: %d", temp_mode)
            
            # Check if running in auto mode
            if mode in (M70RunMode.MEM, M70RunMode.DNC):
                ret2, auto_status = self._mel_get_data(35, 20, system_no, 0, M70DataType.T_DLONG)
                if ret2 == 0 and auto_status == 1:
                    status = M70DeviceStatus.RUN
                    M70Logger.debug("CNC device status: Running")
            elif mode >= M70RunMode.LNK and mode <= M70RunMode.LIN:
                status = M70DeviceStatus.DEBUG
                M70Logger.debug("CNC device status: Debugging")
            
            # Read run status
            ret3, temp_status = self._mel_get_data(35, 10, system_no, 0, M70DataType.T_SHORT)
            if ret3 == 0:
                run_status = M70RunStatus(temp_status)
                M70Logger.debug("CNC running status: %d", temp_status)
                if run_status == M70RunStatus.EMG:
                    status = M70DeviceStatus.STOP
                    M70Logger.warning("CNC device is in emergency stop state")
            
            M70Logger.info("Successfully read CNC status: system_no=%d, status=%d, mode=%d, run_status=%d",
                         system_no, status, mode, run_status)
            return M70ErrorCode.OK, status, mode, run_status
        else:
            M70ErrorHandler.set_error(M70ErrorCode.FAILED, "Failed to read CNC mode")
            M70Logger.error("Failed to read CNC status: Unable to get running mode")
            return M70ErrorCode.FAILED, status, mode, run_status
    
    def read_counter(self, system_no: int = 1) -> Tuple[M70ErrorCode, int]:
        """Read counter"""
        ret, counter = self._mel_get_data(126, 8002, system_no, 0, M70DataType.T_LONG)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, counter
    
    def read_system_count(self) -> Tuple[M70ErrorCode, int]:
        """Read system count"""
        return self._read_count(2, 1)
    
    def read_nc_axis_count(self) -> Tuple[M70ErrorCode, int]:
        """Read NC axis count"""
        return self._read_count(2, 2)
    
    def read_all_axis_count(self) -> Tuple[M70ErrorCode, int]:
        """Read all axis count"""
        return self._read_count(2, 3)
    
    def read_spindle_axis_count(self) -> Tuple[M70ErrorCode, int]:
        """Read spindle axis count"""
        return self._read_count(2, 4)
    
    def read_plc_axis_count(self) -> Tuple[M70ErrorCode, int]:
        """Read PLC axis count"""
        return self._read_count(2, 5)
    
    def _read_count(self, section: int, param: int) -> Tuple[M70ErrorCode, int]:
        """Internal method to read various counts"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        ret, count = self._mel_get_data(section, param, 0, 0, M70DataType.T_CHAR)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, count & 0xFF
    
    def read_nc_type(self) -> Tuple[M70ErrorCode, M70NCMachineType]:
        """Read NC machine type"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, M70NCMachineType.MC
        
        ret, temp = self._mel_get_data(2, 100, 0, 0, M70DataType.T_CHAR)
        if ret == 0:
            machine_type = M70NCMachineType.LATHE if (temp & 0xFF) == 1 else M70NCMachineType.MC
            return M70ErrorCode.OK, machine_type
        return M70ErrorCode.FAILED, M70NCMachineType.MC
    
    def read_nc_version(self) -> Tuple[M70ErrorCode, str]:
        """Read NC version"""
        return self._read_version(67, 1)
    
    def read_nc_name_version(self) -> Tuple[M70ErrorCode, str]:
        """Read NC name version"""
        return self._read_version(68, 1)
    
    def read_plc_version(self) -> Tuple[M70ErrorCode, str]:
        """Read PLC version"""
        return self._read_version(67, 2)
    
    def _read_version(self, section: int, sub_section: int) -> Tuple[M70ErrorCode, str]:
        """Internal method to read version strings"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, ""
        
        ret, data = self._mel_get_data(section, sub_section, 0, 0, M70DataType.T_STR)
        if ret == 0 and isinstance(data, bytes):
            try:
                version = data.decode('utf-8', errors='ignore').rstrip('\x00')
                return M70ErrorCode.OK, version
            except:
                return M70ErrorCode.OK, data.hex()
        return M70ErrorCode.FAILED, ""
    
    def read_main_program_name(self, system_no: int = 1, 
                               name_type: ProgramNameType = ProgramNameType.PROGRAM_NO) -> Tuple[M70ErrorCode, str]:
        """Read main program name"""
        return self._read_program_name(35, 101, system_no, name_type)
    
    def read_sub_program_name(self, system_no: int = 1,
                             name_type: ProgramNameType = ProgramNameType.PROGRAM_NO) -> Tuple[M70ErrorCode, str]:
        """Read sub program name"""
        return self._read_program_name(35, 102, system_no, name_type)
    
    def _read_program_name(self, section: int, base_sub: int, system_no: int, 
                          name_type: ProgramNameType) -> Tuple[M70ErrorCode, str]:
        """Internal method to read program names"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, ""
        
        sub_section = base_sub + int(name_type)
        ret, data = self._mel_get_data(section, sub_section, system_no, 0, M70DataType.T_STR)
        if ret == 0 and isinstance(data, bytes):
            try:
                prog_name = data.decode('utf-8', errors='ignore').rstrip('\x00')
                return M70ErrorCode.OK, prog_name
            except:
                return M70ErrorCode.OK, ""
        return M70ErrorCode.FAILED, ""
    
    def read_axis_position(self, system_no: int, axis_index: int, 
                          pos_type: PositionType) -> Tuple[M70ErrorCode, float]:
        """Read single axis position"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0.0
        
        axis_flag = 1 << (axis_index - 1) if axis_index >= 1 else 0
        ret, pos = self._mel_get_data(36, int(pos_type), system_no, axis_flag, M70DataType.T_DOUBLE)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, float(pos) if isinstance(pos, (int, float)) else 0.0
    
    def read_all_axis_position(self, system_no: int, pos_type: PositionType) -> Tuple[M70ErrorCode, List[float]]:
        """Read all axes positions"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, []
        
        # First get axis count
        ret, axis_count = self.read_nc_axis_count()
        if ret != M70ErrorCode.OK:
            return M70ErrorCode.FAILED, []
        
        positions = []
        for i in range(1, axis_count + 1):
            ret, pos = self.read_axis_position(system_no, i, pos_type)
            if ret == M70ErrorCode.OK:
                positions.append(pos)
            else:
                positions.append(0.0)
        
        return M70ErrorCode.OK, positions
    
    def read_axis_name(self, system_no: int = 1) -> Tuple[M70ErrorCode, str, int]:
        """Read axis names"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, "", 0
        
        ret, data = self._mel_get_data(36, 100, system_no, 0, M70DataType.T_STR)
        if ret == 0 and isinstance(data, bytes):
            try:
                names = data.decode('utf-8', errors='ignore').rstrip('\x00')
                axis_count = len([c for c in names if c.isalpha()])
                return M70ErrorCode.OK, names, axis_count
            except:
                return M70ErrorCode.OK, "", 0
        return M70ErrorCode.FAILED, "", 0
    
    def read_spindle_speed(self, system_no: int = 1, axis_index: int = 1) -> Tuple[M70ErrorCode, int]:
        """Read spindle speed"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        axis_flag = 1 << (axis_index - 1) if axis_index >= 1 else 0
        ret, speed = self._mel_get_data(37, 5, system_no, axis_flag, M70DataType.T_LONG)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, speed
    
    def read_spindle_override(self, system_no: int = 1) -> Tuple[M70ErrorCode, int]:
        """Read spindle override"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        ret, override = self._mel_get_data(37, 1, system_no, 0, M70DataType.T_SHORT)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, override
    
    def read_spindle_load(self, system_no: int = 1, axis_index: int = 1, 
                         is_abs: bool = False) -> Tuple[M70ErrorCode, int]:
        """Read spindle load"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        axis_flag = 1 << (axis_index - 1) if axis_index >= 1 else 0
        sub_section = 7 if is_abs else 6
        ret, load = self._mel_get_data(37, sub_section, system_no, axis_flag, M70DataType.T_LONG)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, load
    
    def read_feed_speed(self, system_no: int = 1, 
                       speed_type: FeedSpeedType = FeedSpeedType.FC) -> Tuple[M70ErrorCode, float]:
        """Read feed speed"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0.0
        
        ret, speed = self._mel_get_data(36, 10 + int(speed_type), system_no, 0, M70DataType.T_DOUBLE)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, float(speed) if isinstance(speed, (int, float)) else 0.0
    
    def read_feed_override(self, system_no: int = 1) -> Tuple[M70ErrorCode, int]:
        """Read feed override"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        ret, override = self._mel_get_data(36, 1, system_no, 0, M70DataType.T_SHORT)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, override
    
    def read_current_tool_no(self, system_no: int = 1) -> Tuple[M70ErrorCode, int]:
        """Read current tool number"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        ret, tool_no = self._mel_get_data(35, 1, system_no, 0, M70DataType.T_LONG)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, tool_no
    
    def read_power_on_time(self) -> Tuple[M70ErrorCode, int]:
        """Read power on time (minutes)"""
        return self._read_time(126, 8007)
    
    def read_auto_operation_time(self) -> Tuple[M70ErrorCode, int]:
        """Read auto operation time (minutes)"""
        return self._read_time(126, 8008)
    
    def read_auto_startup_time(self) -> Tuple[M70ErrorCode, int]:
        """Read auto startup time (minutes)"""
        return self._read_time(126, 8009)
    
    def read_cycle_time(self) -> Tuple[M70ErrorCode, int]:
        """Read cycle time (seconds)"""
        return self._read_time(126, 8010)
    
    def read_cutting_time(self) -> Tuple[M70ErrorCode, int]:
        """Read cutting time (seconds)"""
        return self._read_time(126, 8011)
    
    def _read_time(self, section: int, sub_section: int) -> Tuple[M70ErrorCode, int]:
        """Internal method to read time values"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        ret, time_val = self._mel_get_data(section, sub_section, 0, 0, M70DataType.T_LONG)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, time_val
    
    def read_system_datetime(self) -> Tuple[M70ErrorCode, int, int]:
        """Read system date and time"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0, 0
        
        ret1, date = self._mel_get_data(126, 8101, 0, 0, M70DataType.T_LONG)
        ret2, time = self._mel_get_data(126, 8102, 0, 0, M70DataType.T_LONG)
        
        if ret1 == 0 and ret2 == 0:
            return M70ErrorCode.OK, date, time
        return M70ErrorCode.FAILED, 0, 0
    
    # ==================== Internal Helper Methods ====================
    
    def _mel_get_data(self, section: int, sub_section: int, system_no: int, 
                     axis_flag: int, data_type: M70DataType) -> Tuple[int, any]:
        """
        Internal method to get data from CNC
        Returns: (error_code, data)
        """
        if not self.is_connected():
            return -1, 0
        
        try:
            # Build request packet
            giop_header = M70GIOP.build_giop_header(self)
            # operation_length should be string length + null terminator (13 for "mochaGetData\0")
            request_header = M70GIOP.build_request_header(self, len(M70GIOP.OP_GET_DATA) + 1)
            
            # Build data packet - op field must be exactly 16 bytes (padded with zeros)
            packet = bytearray()
            op_field = bytearray(16)  # Fixed size buffer
            op_bytes = M70GIOP.OP_GET_DATA + b'\x00'  # Add null terminator
            op_field[:len(op_bytes)] = op_bytes  # Copy and pad with zeros
            packet.extend(op_field)
            
            packet.extend(struct.pack('<I', 0))  # principal
            packet.extend(struct.pack('<I', section))  # Use unsigned int
            packet.extend(struct.pack('<I', sub_section))  # Use unsigned int
            packet.extend(struct.pack('<I', system_no))  # Use unsigned int
            packet.extend(struct.pack('<I', axis_flag))  # Use unsigned int
            packet.extend(struct.pack('<I', 0))  # u2
            packet.extend(struct.pack('<I', data_type))
            
            # Update GIOP header with correct length
            data_length = len(request_header) + len(packet)
            full_packet = bytearray(giop_header)
            struct.pack_into('<I', full_packet, 8, data_length)
            full_packet.extend(request_header)
            full_packet.extend(packet)
            
            # Send request
            if M70Socket.send_data(self._socket_obj, bytes(full_packet)) < 0:
                return -1, 0
            
            # Receive response
            error_code, remaining_length = M70GIOP.receive_response(self)
            if error_code != 0:
                return error_code, 0
            
            # Parse response data
            if remaining_length > 0:
                data = self._parse_get_data_response(data_type, remaining_length)
                return 0, data
            
            return 0, 0
            
        except Exception as e:
            M70Logger.error("Error in _mel_get_data: %s", str(e))
            return -1, 0
    
    def _parse_get_data_response(self, data_type: M70DataType, length: int) -> any:
        """Parse get data response"""
        try:
            # Receive response header (12 bytes)
            header = M70Socket.recv_data(self._socket_obj, 12)
            if not header or len(header) < 12:
                return 0
            
            u1 = struct.unpack('<I', header[0:4])[0]
            resp_data_type = struct.unpack('<I', header[4:8])[0]
            data_length = struct.unpack('<I', header[8:12])[0]
            
            if data_length == 0:
                return 0
            
            # Receive actual data
            data_bytes = M70Socket.recv_data(self._socket_obj, data_length)
            if not data_bytes:
                return 0
            
            # Parse based on data type
            if resp_data_type == M70DataType.T_CHAR or resp_data_type == M70DataType.T_UCHAR:
                return struct.unpack('<B', data_bytes[0:1])[0]
            elif resp_data_type == M70DataType.T_SHORT or resp_data_type == M70DataType.T_USHORT:
                return struct.unpack('<H', data_bytes[0:2])[0]
            elif resp_data_type == M70DataType.T_LONG or resp_data_type == M70DataType.T_UINT32:
                return struct.unpack('<I', data_bytes[0:4])[0]
            elif resp_data_type == M70DataType.T_DLONG:
                return struct.unpack('<Q', data_bytes[0:8])[0]
            elif resp_data_type == M70DataType.T_DOUBLE:
                return struct.unpack('<d', data_bytes[0:8])[0]
            elif resp_data_type >= M70DataType.T_STR:
                return data_bytes
            else:
                return data_bytes
                
        except Exception as e:
            M70Logger.error("Error parsing response: %s", str(e))
            return 0
