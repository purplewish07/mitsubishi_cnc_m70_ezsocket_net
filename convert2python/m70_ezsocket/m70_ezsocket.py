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
        return self._read_program_name(45, 101, system_no, name_type)
    
    def read_sub_program_name(self, system_no: int = 1,
                             name_type: ProgramNameType = ProgramNameType.PROGRAM_NO) -> Tuple[M70ErrorCode, str]:
        """Read sub program name"""
        return self._read_program_name(45, 102, system_no, name_type)
    
    def read_program_file_info(self, system_no: int = 1, 
                               info_type: M70FileInfoType = M70FileInfoType.REG_PROG_NOS) -> Tuple[M70ErrorCode, int]:
        """Read program file information
        Returns number based on info_type:
        - REG_PROG_NOS: Number of registered machining programs
        - USED_PROG_NOS: Remaining machining programs
        - CAPA_CHAR_NOS: Machining program character capacity
        - FREE_CHAR_NOS: Remaining characters in machining program
        - TRANS_SIZE: Transfer data size for melCopyFile
        """
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        # Map info_type to subsection
        sub_section_map = {
            M70FileInfoType.REG_PROG_NOS: 1,
            M70FileInfoType.USED_PROG_NOS: 2,
            M70FileInfoType.CAPA_CHAR_NOS: 3,
            M70FileInfoType.FREE_CHAR_NOS: 4,
            M70FileInfoType.TRANS_SIZE: 10
        }
        
        sub_section = sub_section_map.get(info_type, 1)
        ret, data = self._mel_get_data(25, sub_section, system_no, 0, M70DataType.T_DLONG)
        
        if ret == 0:
            return M70ErrorCode.OK, data
        return M70ErrorCode.FAILED, 0
    
    def read_program_block(self, system_no: int = 1, row_count: int = 10) -> Tuple[M70ErrorCode, str]:
        """Read current program block"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, ""
        
        try:
            # Call GIOP layer method
            error_code, prog_block_data = M70GIOP.mel_get_current_prg_block(self, system_no, row_count)
            
            if error_code != 0 or not prog_block_data:
                return M70ErrorCode.FAILED, ""
            
            # Parse prog_block structure
            # Structure: int32 current_block, int32 current_row, int32 u1, int32 block_length, byte text[512]
            if len(prog_block_data) >= 16:
                current_block, current_row, u1_field, block_length = struct.unpack('<iiii', prog_block_data[0:16])
                if block_length > 0:
                    text = prog_block_data[16:16+min(block_length, len(prog_block_data)-16)]
                    result_text = text.decode('utf-8', errors='ignore').rstrip('\x00')
                    return M70ErrorCode.OK, result_text
            
            return M70ErrorCode.FAILED, ""
            
        except Exception as e:
            M70Logger.error("Error in read_program_block: %s", str(e))
            return M70ErrorCode.FAILED, ""
    
    def read_alarm(self, system_no: int = 1, msg_count: int = 10, 
                   alarm_type: 'AlarmType' = None) -> Tuple[M70ErrorCode, List[str]]:
        """Read current alarm messages"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, []
        
        if alarm_type is None:
            from .typedef import AlarmType
            alarm_type = AlarmType.ALL_ALARM
        
        try:
            # Call GIOP layer method
            error_code, alarm_data = M70GIOP.mel_get_current_alarm_msg(self, system_no, msg_count, int(alarm_type))
            
            if error_code != 0 or not alarm_data:
                return M70ErrorCode.FAILED, []
            
            # Parse alarm response - has 12 byte header
            alarms = []
            if len(alarm_data) >= 12:
                # Response header: 12 bytes
                header = alarm_data[:12]
                u1, resp_data_type, data_length = struct.unpack('<III', header)
                
                if data_length > 0 and len(alarm_data) >= 12 + data_length:
                    # alarm_string structure: int32 alarm_no, int32 alarm_length, byte text[256] (repeated)
                    data_bytes = alarm_data[12:12+data_length]
                    offset = 0
                    while offset + 8 <= len(data_bytes):
                        alarm_no, alarm_length = struct.unpack('<ii', data_bytes[offset:offset+8])
                        offset += 8
                        if alarm_length > 0 and offset + alarm_length <= len(data_bytes):
                            text = data_bytes[offset:offset+min(alarm_length, 256)]
                            alarm_text = text.decode('utf-8', errors='ignore').rstrip('\x00')
                            alarms.append(alarm_text)
                            offset += 256  # Fixed size in structure
                        else:
                            break
            
            return M70ErrorCode.OK, alarms
            
        except Exception as e:
            M70Logger.error("Error in read_alarm: %s", str(e))
            return M70ErrorCode.FAILED, []
    
    def _read_program_name(self, section: int, base_sub: int, system_no: int, 
                          name_type: ProgramNameType) -> Tuple[M70ErrorCode, str]:
        """Internal method to read program names"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, ""
        
        sub_section = base_sub + int(name_type)
        
        # SequenceNumber and BlockNumber use T_DLONG, others use T_STR
        if name_type == ProgramNameType.SEQUENCE_NUMBER or name_type == ProgramNameType.BLOCK_NUMBER:
            ret, data = self._mel_get_data(section, sub_section, system_no, 0, M70DataType.T_DLONG)
            if ret == 0:
                return M70ErrorCode.OK, str(data)
            return M70ErrorCode.FAILED, ""
        else:
            ret, data = self._mel_get_data(section, sub_section, system_no, 0, M70DataType.T_STR)
            if ret == 0 and isinstance(data, bytes):
                try:
                    prog_name = data.decode('utf-8', errors='ignore').rstrip('\x00')
                    return M70ErrorCode.OK, prog_name
                except:
                    return M70ErrorCode.OK, ""
            return M70ErrorCode.FAILED, ""
    
    def read_svo_load(self, system_no: int = 1, axis_index: int = 1, 
                     is_abs: bool = False) -> Tuple[M70ErrorCode, int]:
        """Read servo load
        Args:
            system_no: System number (default 1)
            axis_index: Axis index (1-based)
            is_abs: If True, return absolute value
        Returns:
            Tuple of (error_code, servo_load)
        """
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        axis_flag = 1 << (axis_index - 1) if axis_index >= 1 else 0
        ret, load = self._mel_get_data(59, 4, system_no, axis_flag, M70DataType.T_SHORT)
        
        if ret == 0:
            load = abs(load) if is_abs else load
            return M70ErrorCode.OK, load
        return M70ErrorCode.FAILED, 0
    
    def read_axis_position(self, system_no: int, axis_index: int, 
                          pos_type: PositionType) -> Tuple[M70ErrorCode, float]:
        """Read single axis position"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0.0
        
        # Map position type enum to subsection value (add 1)
        # POS_WRK(0)->1, POS_MCH(1)->2, POS_CURRENT(2)->3, POS_RELATV(3)->4, POS_PROGRAM(4)->5, DISTANCE(5)->6
        subsection = int(pos_type) + 1
        
        axis_flag = self._get_axis_real_no(axis_index)
        ret, pos = self._mel_get_data(37, subsection, system_no, axis_flag, M70DataType.T_FLOATBIN)
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
        
        # First, read axis count from (2, 2)
        ret, axis_count = self._mel_get_data(2, 2, 0, 0, M70DataType.T_CHAR)
        if ret != 0:
            return M70ErrorCode.FAILED, "", 0
        
        # Then read each axis name from (127, 1)
        names = []
        for i in range(1, axis_count + 1):
            axis_flag = self._get_axis_real_no(i)
            ret, data = self._mel_get_data(127, 1, system_no, axis_flag, M70DataType.T_STR)
            if ret == 0 and isinstance(data, bytes):
                try:
                    name = data.decode('utf-8', errors='ignore').rstrip('\x00')
                    # Extract just the axis name (first few characters)
                    if name:
                        names.append(name.split()[0] if ' ' in name else name)
                except:
                    pass
        
        axis_names = ','.join(names) if names else ""
        return M70ErrorCode.OK, axis_names, len(names)
    
    def _get_axis_real_no(self, axis_index: int) -> int:
        """Convert axis index to real axis number (bit flag)"""
        return (1 << (axis_index - 1)) if axis_index >= 1 else 0
    
    def read_spindle_speed(self, system_no: int = 1, axis_index: int = 1) -> Tuple[M70ErrorCode, int]:
        """Read spindle speed"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        axis_flag = self._get_axis_real_no(axis_index)
        ret, speed = self._mel_get_data(34, 1, system_no, axis_flag, M70DataType.T_DLONG)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, speed
    
    def read_spindle_override(self, system_no: int = 1) -> Tuple[M70ErrorCode, int]:
        """Read spindle override
        Uses Y188F to determine method:
        - If bType==0: Use Y1888 code mapping
        - Otherwise: Use R7008 direct value
        """
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        temp = 0
        # Y188F: Spindle override setting method selection
        # First spindle {(4 axes) difference 96} Second axis Y18EF
        sub_section = 16287 + 96 * (system_no - 1)
        ret1, b_type = self._mel_get_data(53, sub_section, 0, 0, M70DataType.T_CHAR)
        
        if ret1 == 0:
            if b_type == 0:
                # Y1888 SP11: Spindle override code 1
                # First spindle {(6 spindles) difference 96} Second axis Y18E8
                ret2, code = self._mel_get_data(54, 16280 + 96 * (system_no - 1), 0, 0, M70DataType.T_UCHAR)
                if ret2 == 0:
                    # Map code to percentage
                    code_map = {
                        0x7: 50, 0x3: 60, 0x2: 70, 0x6: 80,
                        0x4: 90, 0x1: 110, 0x5: 120, 0x0: 100
                    }
                    temp = code_map.get(code, 100)
                    return M70ErrorCode.OK, temp
            else:
                # R7008: S command override
                # First spindle {(6 spindles) difference 50} Second axis R7058
                ret3, value = self._mel_get_data(55, 107008 + 50 * (system_no - 1), 0, 0, M70DataType.T_SHORT)
                if ret3 == 0:
                    return M70ErrorCode.OK, value
        
        return M70ErrorCode.FAILED, 0
    
    def read_spindle_load(self, system_no: int = 1, axis_index: int = 1, 
                         is_abs: bool = False) -> Tuple[M70ErrorCode, int]:
        """Read spindle load"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        axis_flag = 1 << (axis_index - 1) if axis_index >= 1 else 0
        ret, load = self._mel_get_data(63, 4, system_no, axis_flag, M70DataType.T_DLONG)
        if ret == 0:
            load = abs(load) if is_abs else load
            return M70ErrorCode.OK, load
        return M70ErrorCode.FAILED, 0
    
    def read_feed_speed(self, system_no: int = 1, 
                       speed_type: FeedSpeedType = FeedSpeedType.FC) -> Tuple[M70ErrorCode, float]:
        """Read feed speed
        FA/FM/FS/FE: section 42, subsection 1/2/3/4
        FC: section 33, subsection 1
        Returns float_bin_data (16 bytes)
        """
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0.0
        
        # Map speed type to section/subsection
        if speed_type == FeedSpeedType.FA:
            section, sub_section = 42, 1
        elif speed_type == FeedSpeedType.FM:
            section, sub_section = 42, 2
        elif speed_type == FeedSpeedType.FS:
            section, sub_section = 42, 3
        elif speed_type == FeedSpeedType.FE:
            section, sub_section = 42, 4
        else:  # FC
            section, sub_section = 33, 1
        
        ret, speed = self._mel_get_data(section, sub_section, system_no, 0, M70DataType.T_FLOATBIN)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, float(speed) if isinstance(speed, (int, float)) else 0.0
    
    def read_feed_override(self, system_no: int = 1) -> Tuple[M70ErrorCode, int]:
        """Read feed override
        Uses YC67 to determine method:
        - If bType==0: Use YC60 calculation (0x0F-(bType&0x0F))*10
        - Otherwise: Use R2500 direct value
        """
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        temp_override = 0
        # YC67: Cutting feed override value setting method
        # First system {(4 systems) difference 320} Second axis YDA7
        sub_section = 13175 + 320 * (system_no - 1)
        ret1, b_type = self._mel_get_data(53, sub_section, 0, 0, M70DataType.T_CHAR)
        
        if ret1 == 0:
            if b_type == 0:
                # YC60: Cutting feed override code 1
                # First system {(4 systems) difference 320} Second axis YDA0
                ret2, code = self._mel_get_data(54, 13168 + 320 * (system_no - 1), 0, 0, M70DataType.T_CHAR)
                if ret2 == 0:
                    temp_override = (0x0F - (code & 0x0F)) * 10
                    return M70ErrorCode.OK, temp_override
            else:
                # R2500: First cutting feed override
                # First system {(4 systems) difference 200} Second axis R2700
                ret3, value = self._mel_get_data(55, 102500 + 200 * (system_no - 1), 0, 0, M70DataType.T_SHORT)
                if ret3 == 0:
                    return M70ErrorCode.OK, value
        
        return M70ErrorCode.FAILED, 0
    
    def read_current_tool_no(self, system_no: int = 1) -> Tuple[M70ErrorCode, int]:
        """Read current tool number"""
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0
        
        # R536 parameter: section 55, subsection 100536, T_SHORT
        ret, tool_no = self._mel_get_data(55, 100536, system_no, 0, M70DataType.T_SHORT)
        return M70ErrorCode.OK if ret == 0 else M70ErrorCode.FAILED, tool_no
    
    def read_power_on_time(self) -> Tuple[M70ErrorCode, int]:
        """Read power on time (minutes)"""
        return self._read_time(40, 1)
    
    def read_auto_operation_time(self) -> Tuple[M70ErrorCode, int]:
        """Read auto operation time (minutes)"""
        return self._read_time(40, 2)
    
    def read_auto_startup_time(self) -> Tuple[M70ErrorCode, int]:
        """Read auto startup time (minutes)"""
        return self._read_time(40, 3)
    
    def read_cycle_time(self) -> Tuple[M70ErrorCode, int]:
        """Read cycle time (seconds)"""
        return self._read_time(40, 8)
    
    def read_cutting_time(self) -> Tuple[M70ErrorCode, int]:
        """Read cutting time (seconds)"""
        return self._read_time(40, 100)
    
    def read_external_accumulative_time(self) -> Tuple[M70ErrorCode, int, int]:
        """Read external accumulative time
        Returns:
            Tuple of (error_code, time1, time2) where time1 and time2 are in minutes
        """
        if not self.is_connected():
            return M70ErrorCode.FAILED, 0, 0
        
        ret1, time1 = self._mel_get_data(40, 4, 0, 0, M70DataType.T_UINT32)
        ret2, time2 = self._mel_get_data(40, 5, 0, 0, M70DataType.T_UINT32)
        
        if ret1 == 0 and ret2 == 0:
            return M70ErrorCode.OK, time1, time2
        return M70ErrorCode.FAILED, 0, 0
    
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
        
        ret1, date = self._mel_get_data(40, 6, 0, 0, M70DataType.T_UINT32)
        ret2, time = self._mel_get_data(40, 7, 0, 0, M70DataType.T_UINT32)
        
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
            elif resp_data_type == M70DataType.T_FLOATBIN:
                # FLOATBIN: short int_data_nos, short dec_data_nos, uint32 option, double data (16 bytes)
                if len(data_bytes) >= 16:
                    int_data_nos, dec_data_nos, option, data = struct.unpack('<hhId', data_bytes[0:16])
                    return data  # Return the double value
                return 0.0
            elif resp_data_type >= M70DataType.T_STR:
                return data_bytes
            else:
                return data_bytes
                
        except Exception as e:
            M70Logger.error("Error parsing response: %s", str(e))
            return 0
    
    # ==================== File System Methods ====================
    
    def read_file(self, filepath: str, max_size: int = 512) -> Tuple[M70ErrorCode, Optional[bytes]]:
        """
        Read file from CNC file system
        Args:
            filepath: File path on CNC (e.g., "//CNC_MEM/USER/PART1.MPF")
            max_size: Maximum bytes to read (default 512)
        Returns: (error_code, file_data)
        """
        try:
            # Open file for reading (mode=0 for read-only)
            error_code, fd = M70GIOP.mel_fs_open_file(self, filepath, 0)
            if error_code != 0 or fd == 0:
                M70Logger.error("Failed to open file: %s", filepath)
                return M70ErrorCode.FAILED, None
            
            # Read file content
            error_code, actual_size, file_data = M70GIOP.mel_fs_read_file(self, fd, max_size)
            
            # Close file
            M70GIOP.mel_fs_close_file(self, fd)
            
            if error_code != 0:
                return M70ErrorCode.FAILED, None
            
            return M70ErrorCode.OK, file_data
            
        except Exception as e:
            M70Logger.error("Error reading file %s: %s", filepath, str(e))
            return M70ErrorCode.FAILED, None
    
    def stat_file(self, filepath: str) -> Tuple[M70ErrorCode, Optional[dict]]:
        """
        Get file status/information
        Args:
            filepath: File path on CNC (e.g., "//CNC_MEM/USER/PART1.MPF")
        Returns: (error_code, file_info_dict)
            file_info_dict contains: mode, file_size, year, month, day, hour, minute, second
        """
        try:
            error_code, file_stat = M70GIOP.mel_fs_stat_file(self, filepath)
            
            if error_code != 0:
                return M70ErrorCode.FAILED, None
            
            return M70ErrorCode.OK, file_stat
            
        except Exception as e:
            M70Logger.error("Error getting file stat %s: %s", filepath, str(e))
            return M70ErrorCode.FAILED, None
    
    def list_directory(self, dirpath: str) -> Tuple[M70ErrorCode, List[str]]:
        r"""
        List directory contents
        Args:
            dirpath: Directory path on CNC (e.g., "//CNC_MEM/USER")
            A file is set with an absolute path as follows:   Drive name + ":" + \Directory name\File name 
        Returns: (error_code, list of filenames)
        """
        try:
            # Open directory
            error_code, fd = M70GIOP.mel_fs_open_directory(self, dirpath)
            if error_code != 0 or fd == 0:
                M70Logger.error("Failed to open directory: %s", dirpath)
                return M70ErrorCode.FAILED, []
            
            # Read directory entries
            entries = []
            while True:
                error_code, dirname = M70GIOP.mel_fs_read_directory(self, fd)
                if error_code != 0 or not dirname:
                    break
                entries.append(dirname)
            
            # Close directory
            M70GIOP.mel_fs_close_directory(self, fd)
            
            return M70ErrorCode.OK, entries
            
        except Exception as e:
            M70Logger.error("Error listing directory %s: %s", dirpath, str(e))
            return M70ErrorCode.FAILED, []
