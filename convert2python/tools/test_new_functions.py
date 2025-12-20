"""
Test script for newly implemented functions:
- read_program_file_info
- read_svo_load
- read_external_accumulative_time
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m70_ezsocket import M70Connection, M70FileInfoType

def test_new_functions():
    # Connect to CNC
    conn = M70Connection("192.168.1.206", 683)
    
    print("Connecting to CNC...")
    if not conn.connect():
        print("Failed to connect to CNC!")
        return
    
    print("Connected successfully!\n")
    
    # Test 1: read_program_file_info
    print("=" * 60)
    print("Test 1: read_program_file_info")
    print("=" * 60)
    
    info_types = [
        (M70FileInfoType.REG_PROG_NOS, "Registered programs"),
        (M70FileInfoType.USED_PROG_NOS, "Used programs"),
        (M70FileInfoType.CAPA_CHAR_NOS, "Character capacity"),
        (M70FileInfoType.FREE_CHAR_NOS, "Free characters"),
        (M70FileInfoType.TRANS_SIZE, "Transfer size")
    ]
    
    for info_type, description in info_types:
        ret, value = conn.read_program_file_info(system_no=1, info_type=info_type)
        print(f"{description}: ret={ret}, value={value}")
    
    # Test 2: read_svo_load
    print("\n" + "=" * 60)
    print("Test 2: read_svo_load")
    print("=" * 60)
    
    # Test for multiple axes
    for axis_index in range(1, 4):  # Test axes 1-3
        ret, load = conn.read_svo_load(system_no=1, axis_index=axis_index, is_abs=False)
        print(f"Axis {axis_index} servo load: ret={ret}, load={load}")
        
        if ret == 0:
            # Also test absolute value
            ret_abs, load_abs = conn.read_svo_load(system_no=1, axis_index=axis_index, is_abs=True)
            print(f"  Absolute: ret={ret_abs}, load={load_abs}")
    
    # Test 3: read_external_accumulative_time
    print("\n" + "=" * 60)
    print("Test 3: read_external_accumulative_time")
    print("=" * 60)
    
    ret, time1, time2 = conn.read_external_accumulative_time()
    print(f"External accumulative time:")
    print(f"  ret={ret}")
    print(f"  time1={time1} minutes ({time1/60:.2f} hours)")
    print(f"  time2={time2} minutes ({time2/60:.2f} hours)")
    
    # Disconnect
    print("\n" + "=" * 60)
    conn.disconnect()
    print("Disconnected from CNC")
    print("=" * 60)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    try:
        test_new_functions()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
