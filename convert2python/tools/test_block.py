import sys
sys.path.insert(0, '.')
from m70_ezsocket import M70Connection, M70NCType, M70Logger, M70LogConfig, M70LogLevel, M70LogTarget

# Enable debug logging
config = M70LogConfig()
config.level = M70LogLevel.DEBUG
config.target = M70LogTarget.CONSOLE
M70Logger.init(config)

conn = M70Connection('192.168.1.206', 683, 6)
print('Connecting...')
if conn.connect():
    print('Connected')
    print(f'Socket connected: {conn.connected}')
    
    ret, ver = conn.read_nc_version()
    print(f'Version: {ver}')
    print(f'Still connected: {conn.connected}')
    
    ret, block = conn.read_program_block(1, 10)
    print(f'Block ret={ret}, data={repr(block[:50]) if block else "empty"}')
    print(f'After block connected: {conn.connected}')
    
    ret, ver2 = conn.read_nc_version()
    print(f'Version after block: {ver2}')
    
    conn.disconnect()
    print('Done')
else:
    print('Failed to connect')

M70Logger.shutdown()
