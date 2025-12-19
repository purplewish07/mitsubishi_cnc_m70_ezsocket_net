"""Debug axis position reading"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from m70_ezsocket import M70Connection
import struct

# Connect
conn = M70Connection('192.168.1.206', 683, 6)
result = conn.connect()
if not result:
    print(f"Connection failed")
    sys.exit(1)

print("Connected successfully!\n")

# Read axis count first
error_code, axis_count = conn._mel_get_data(2, 2, 0, 0, 1)  # T_CHAR
print(f"Axis count: {axis_count}")

# Test reading axis position for each axis
from m70_ezsocket.typedef import M70DataType, PositionType

for axis_index in range(1, axis_count + 1):
    print(f"\n=== Axis {axis_index} ===")
    
    # Get axis flag  
    axis_flag = 1 << (axis_index - 1)
    print(f"Axis flag: 0x{axis_flag:08x}")
    
    # Try to read position using API
    section = 37
    subsection = int(PositionType.POS_PROGRAM)
    system_no = 0
    data_type = M70DataType.T_FLOATBIN
    
    print(f"Calling _mel_get_data({section}, {subsection}, {system_no}, {axis_flag}, {data_type})")
    
    error_code, data = conn._mel_get_data(section, subsection, system_no, axis_flag, data_type)
    print(f"Error code: {error_code}, Data: {data}")

conn.disconnect()
print("\nDisconnected")
