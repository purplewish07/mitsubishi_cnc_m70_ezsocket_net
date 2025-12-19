"""
Test with detailed packet dumping
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from m70_ezsocket import (
    M70Connection, M70Logger, M70LogConfig, M70LogLevel, M70LogTarget,
    M70NCType, M70ErrorCode
)

# Patch send to log packets
import socket
original_send = socket.socket.send
def logged_send(self, data):
    print(f"\n>>> SENDING {len(data)} bytes:")
    print(f"HEX: {data.hex()}")
    if len(data) >= 12:
        print(f"GIOP Magic: {data[0:4]}")
        print(f"GIOP Version: {data[4:6].hex()}")
        print(f"GIOP Byte Order: {data[6]}")
        print(f"GIOP Msg Type: {data[7]}")
    return original_send(self, data)

socket.socket.send = logged_send

original_recv = socket.socket.recv
def logged_recv(self, bufsize):
    data = original_recv(self, bufsize)
    if data:
        print(f"\n<<< RECEIVED {len(data)} bytes:")
        print(f"HEX: {data[:min(len(data), 64)].hex()}")
    return data

socket.socket.recv = logged_recv

def main():
    config = M70LogConfig()
    config.level = M70LogLevel.DEBUG
    config.target = M70LogTarget.CONSOLE
    M70Logger.init(config)
    
    cnc = M70Connection("192.168.1.206", 683, M70NCType.MELDAS700M)
    
    if cnc.connect():
        print("\n========== CONNECTED ==========\n")
        
        # Try to read version
        print("\n========== READING NC VERSION ==========\n")
        ret, nc_version = cnc.read_nc_version()
        print(f"Result: {ret}, Version: {nc_version}")
        
        cnc.disconnect()
    else:
        print("Connection failed")
    
    M70Logger.shutdown()

if __name__ == "__main__":
    main()
