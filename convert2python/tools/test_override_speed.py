#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for override and speed functions
Tests the corrected implementations of:
- read_spindle_override
- read_spindle_load
- read_feed_speed
- read_feed_override
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from m70_ezsocket import M70Connection, M70ErrorCode, FeedSpeedType


def main():
    # Connect to CNC
    ip = "192.168.1.206"
    port = 683
    
    print(f"Connecting to {ip}:{port}...")
    conn = M70Connection(ip, port)
    if not conn.connect():
        print("Connection failed!")
        return 1
    
    print("Connected\n")
    
    system_no = 1
    
    # Test 1: Spindle Override
    print("=" * 50)
    print("Test 1: Spindle Override")
    print("=" * 50)
    ret, override = conn.read_spindle_override(system_no)
    if ret == M70ErrorCode.OK:
        print(f"✓ Spindle Override: {override}%")
    else:
        print(f"✗ Failed to read spindle override")
    
    # Test 2: Spindle Load
    print("\n" + "=" * 50)
    print("Test 2: Spindle Load")
    print("=" * 50)
    for axis_index in [1]:  # Test first axis
        ret, load = conn.read_spindle_load(system_no, axis_index, is_abs=False)
        if ret == M70ErrorCode.OK:
            print(f"✓ Spindle Load (Axis {axis_index}): {load}")
        else:
            print(f"✗ Failed to read spindle load for axis {axis_index}")
        
        ret, load_abs = conn.read_spindle_load(system_no, axis_index, is_abs=True)
        if ret == M70ErrorCode.OK:
            print(f"✓ Spindle Load Abs (Axis {axis_index}): {load_abs}")
        else:
            print(f"✗ Failed to read absolute spindle load for axis {axis_index}")
    
    # Test 3: Feed Speed (all types)
    print("\n" + "=" * 50)
    print("Test 3: Feed Speed")
    print("=" * 50)
    speed_types = [
        (FeedSpeedType.FA, "FA (Actual)"),
        (FeedSpeedType.FM, "FM (Modal)"),
        (FeedSpeedType.FS, "FS (Start)"),
        (FeedSpeedType.FE, "FE (End)"),
        (FeedSpeedType.FC, "FC (Command)"),
    ]
    
    for speed_type, name in speed_types:
        ret, speed = conn.read_feed_speed(system_no, speed_type)
        if ret == M70ErrorCode.OK:
            print(f"✓ Feed Speed {name}: {speed:.3f}")
        else:
            print(f"✗ Failed to read feed speed {name}")
    
    # Test 4: Feed Override
    print("\n" + "=" * 50)
    print("Test 4: Feed Override")
    print("=" * 50)
    ret, override = conn.read_feed_override(system_no)
    if ret == M70ErrorCode.OK:
        print(f"✓ Feed Override: {override}%")
    else:
        print(f"✗ Failed to read feed override")
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print("All corrected functions have been tested.")
    print("Check the output above for any failures marked with ✗")
    
    conn.disconnect()
    print("\nDisconnected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
