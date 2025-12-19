"""
Absolute minimal test - just one request
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from m70_ezsocket import M70Connection, M70NCType
from m70_ezsocket.typedef import M70DataType

cnc = M70Connection("192.168.1.206", 683, M70NCType.MELDAS700M)

if cnc.connect():
    print(f"Connected! Request ID: 0x{cnc.request_id:08x}")
    
    # Just try ONE simple request
    print("\nSending request for NC version (67, 1)...")
    ret, data = cnc._mel_get_data(67, 1, 0, 0, M70DataType.T_STR)
    
    print(f"Return code: {ret} (0x{ret & 0xFFFFFFFF:08x})")
    print(f"Data: {data}")
    
    if ret == 0:
        print("SUCCESS!")
    else:
        print(f"FAILED with error code: 0x{ret & 0xFFFFFFFF:08x}")
    
    cnc.disconnect()
else:
    print("Connection failed")
