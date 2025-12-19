"""
Minimal test - try different section/subsection combinations
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from m70_ezsocket import M70Connection, M70NCType, M70Logger, M70LogConfig, M70LogLevel, M70LogTarget
from m70_ezsocket.typedef import M70DataType

config = M70LogConfig()
config.level = M70LogLevel.INFO
config.target = M70LogTarget.CONSOLE
M70Logger.init(config)

cnc = M70Connection("192.168.1.206", 683, M70NCType.MELDAS700M)

if cnc.connect():
    print("Connected!\n")
    
    # Try reading system count first (this is usually safe)
    print("Test 1: Reading system count (2, 1)...")
    ret, count = cnc._mel_get_data(2, 1, 0, 0, M70DataType.T_SHORT)
    print(f"Result: {ret}, Data: {count}\n")
    
    # Try reading NC type
    print("Test 2: Reading NC type (2, 21)...")
    ret, nc_type = cnc._mel_get_data(2, 21, 0, 0, M70DataType.T_SHORT)
    print(f"Result: {ret}, Data: {nc_type}\n")
    
    # Try reading NC version with correct params
    print("Test 3: Reading NC version (67, 1)...")
    ret, version = cnc._mel_get_data(67, 1, 0, 0, M70DataType.T_STR)
    print(f"Result: {ret}, Data: {version}\n")
    
    cnc.disconnect()
else:
    print("Failed to connect")

M70Logger.shutdown()
