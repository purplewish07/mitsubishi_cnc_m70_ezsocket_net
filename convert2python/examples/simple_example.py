"""
Simple example for M70 CNC communication
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import m70_ezsocket
sys.path.insert(0, str(Path(__file__).parent.parent))

from m70_ezsocket import (
    M70Connection, M70Logger, M70LogConfig, M70LogLevel, M70LogTarget,
    M70NCType, M70ErrorCode
)


def main():
    # Initialize logging (optional)
    config = M70LogConfig()
    config.level = M70LogLevel.INFO
    config.target = M70LogTarget.CONSOLE
    M70Logger.init(config)
    
    # Connect to CNC machine
    cnc = M70Connection("192.168.1.214", 683, M70NCType.MELDAS700M)
    
    if not cnc.connect():
        print("Failed to connect to CNC machine")
        return
    
    print("Connected successfully!")
    
    # Read CNC version
    ret, version = cnc.read_nc_version()
    if ret == M70ErrorCode.OK:
        print(f"✓ CNC Version: {version}")
    else:
        print(f"✗ Failed to read NC version (error: {ret})")
    
    # Read CNC status
    ret, status, mode, run_status = cnc.read_status()
    if ret == M70ErrorCode.OK:
        print(f"✓ Status: {status}, Mode: {mode}, Run Status: {run_status}")
    else:
        print(f"✗ Failed to read status (error: {ret})")
    
    # Read axis names and positions
    ret, axis_names, axis_count = cnc.read_axis_name()
    if ret == M70ErrorCode.OK:
        print(f"✓ Axis Names: {axis_names} (Count: {axis_count})")
    else:
        print(f"✗ Failed to read axis names (error: {ret})")
    
    # Read axis positions (workpiece coordinates)
    from m70_ezsocket.typedef import PositionType
    ret, positions = cnc.read_all_axis_position(1, PositionType.POS_WRK)
    if ret == M70ErrorCode.OK:
        print(f"✓ Axis Positions: {positions}")
    else:
        print(f"✗ Failed to read axis positions (error: {ret})")
    
    # Read spindle speed
    ret, speed = cnc.read_spindle_speed()
    if ret == M70ErrorCode.OK:
        print(f"✓ Spindle Speed: {speed} RPM")
    else:
        print(f"✗ Failed to read spindle speed (error: {ret})")
    
    # Read current tool number
    ret, tool_no = cnc.read_current_tool_no()
    if ret == M70ErrorCode.OK:
        print(f"✓ Current Tool: T{tool_no}")
    else:
        print(f"✗ Failed to read current tool (error: {ret})")
    
    # Disconnect
    cnc.disconnect()
    print("Disconnected")
    
    M70Logger.shutdown()


if __name__ == "__main__":
    main()
