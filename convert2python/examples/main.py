"""
Example program for M70 CNC communication
Converted from main.c
"""

import time
import sys
from pathlib import Path

# Add parent directory to path so we can import m70_ezsocket
sys.path.insert(0, str(Path(__file__).parent.parent))

from m70_ezsocket import (
    M70Connection, M70Logger, M70LogConfig, M70LogLevel, M70LogTarget,
    M70NCType, M70ErrorCode, PositionType
)


# Configuration constants
DEFAULT_IP = "192.168.123.130"
DEFAULT_PORT = 683
TEST_COUNT = 5000
TEST_SLEEP_TIME = 2


def log_system_init():
    """Initialize the logging system"""
    config = M70LogConfig()
    config.level = M70LogLevel.WARNING
    config.target = M70LogTarget.FILE
    config.log_file_path = "./logs/mitsubishi_cnc.log"
    config.include_timestamp = True
    config.include_level = True
    config.include_file_line = True
    config.max_file_size = 10 * 1024 * 1024  # 10MB
    config.max_file_count = 5
    
    if not M70Logger.init(config):
        print("Failed to initialize logging system")
        sys.exit(1)
    
    M70Logger.info("Log system initialized successfully")


def read_basic_info(conn: M70Connection) -> int:
    """Read basic information from CNC"""
    failed_count = 0
    
    # Read CNC version information
    ret, nc_version = conn.read_nc_version()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"CNC version: {nc_version}")
    
    ret, nc_name_version = conn.read_nc_name_version()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"CNC name version: {nc_name_version}")
    
    ret, nc_plc_version = conn.read_plc_version()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"CNC PLC version: {nc_plc_version}")
    
    # Read machine type and system information
    ret, nc_type = conn.read_nc_type()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"NC type: {nc_type}")
    
    ret, sys_count = conn.read_system_count()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"System count: {sys_count}")
    
    # Read axis count information
    ret, nc_axis_count = conn.read_nc_axis_count()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"NC axis count: {nc_axis_count}")
    
    ret, sp_axis_count = conn.read_spindle_axis_count()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"NC spindle axis count: {sp_axis_count}")
    
    ret, all_axis_count = conn.read_all_axis_count()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"NC all axis count: {all_axis_count}")
    
    # Read running status
    ret, status, mode, run_status = conn.read_status(1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"NC status: {status}, mode: {mode}, run status: {run_status}")
    
    # Read program information
    ret, main_prog = conn.read_main_program_name(1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Main prog: {main_prog}")
    
    ret, sub_prog = conn.read_sub_program_name(1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Sub prog: {sub_prog}")
    
    # Read tool number
    ret, tool_no = conn.read_current_tool_no(1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Tool no: {tool_no}")
    
    # Read counter
    ret, counter = conn.read_counter(1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Counter: {counter}")
    
    # Read spindle information
    ret, sp_override = conn.read_spindle_override(1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Spindle override: {sp_override}")
    
    ret, sp_load = conn.read_spindle_load(1, 1, False)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Spindle load: {sp_load}")
    
    ret, sp_speed = conn.read_spindle_speed(1, 1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Spindle speed: {sp_speed}")
    
    # Read feed information
    ret, feed_override = conn.read_feed_override(1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Feed override: {feed_override}")
    
    ret, feed_speed = conn.read_feed_speed(1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Feed speed: {feed_speed}")
    
    # Read time information
    ret, power_on_time = conn.read_power_on_time()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Power on time: {power_on_time}")
    
    ret, auto_op_time = conn.read_auto_operation_time()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Auto operation time: {auto_op_time}")
    
    ret, auto_startup_time = conn.read_auto_startup_time()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Auto startup time: {auto_startup_time}")
    
    ret, cycle_time = conn.read_cycle_time()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Cycle time: {cycle_time}")
    
    ret, cutting_time = conn.read_cutting_time()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"Cutting time: {cutting_time}")
    
    ret, sys_date, sys_time = conn.read_system_datetime()
    if ret != M70ErrorCode.OK:
        failed_count += 1
    print(f"System date time: {sys_date}, {sys_time}")
    
    return failed_count


def read_axis_position_info(conn: M70Connection) -> int:
    """Read axis position information"""
    failed_count = 0
    
    # Get axis names
    ret, axis_names, axis_count = conn.read_axis_name(1)
    if ret != M70ErrorCode.OK:
        failed_count += 1
        return failed_count
    
    print(f"Axis:\t {axis_names}")
    
    # Read positions for different types
    pos_types = [
        (PositionType.POS_PROGRAM, "POS_PROGRAM"),
        (PositionType.POS_RELATV, "POS_RELATV"),
        (PositionType.POS_WRK, "POS_WRK"),
        (PositionType.POS_MCH, "POS_MCH"),
        (PositionType.DISTANCE, "DISTANCE")
    ]
    
    for pos_type, type_name in pos_types:
        ret, positions = conn.read_all_axis_position(1, pos_type)
        if ret != M70ErrorCode.OK:
            failed_count += 1
            continue
        
        print(f"{type_name}:\t", end="")
        for pos in positions:
            print(f"{pos:.3f}\t", end="")
        print()
    
    return failed_count


def main():
    """Main function"""
    # Initialize logging system
    log_system_init()
    
    # Get connection parameters
    plc_ip = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IP
    plc_port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    
    print(f"Connecting to {plc_ip}:{plc_port}...")
    
    # Create connection and connect
    conn = M70Connection(plc_ip, plc_port, M70NCType.MELDAS700M)
    if not conn.connect():
        print("Failed to connect to CNC machine")
        M70Logger.shutdown()
        return -1
    
    print("Successfully connected to CNC machine")
    
    # Execute test loop
    total_failed_count = 0
    
    try:
        for i in range(TEST_COUNT):
            print(f"===================== [{i}] ===================")
            
            # Read basic information
            failed_count = read_basic_info(conn)
            total_failed_count += failed_count
            
            print("------------------------ TEST AXIS ----------------------")
            
            # Read axis information
            failed_count = read_axis_position_info(conn)
            total_failed_count += failed_count
            
            # Sleep between iterations
            time.sleep(TEST_SLEEP_TIME)
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    finally:
        print(f"\nAll Failed count: {total_failed_count}")
        
        # Clean up resources
        conn.disconnect()
        
        # Close log system
        M70Logger.info("Example program ended, closing log system")
        M70Logger.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
