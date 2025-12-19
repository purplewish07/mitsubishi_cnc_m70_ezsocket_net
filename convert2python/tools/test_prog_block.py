import sys
sys.path.insert(0, '..')
sys.path.insert(0, '.')
from m70_ezsocket import M70Connection, M70NCType, M70Logger, M70LogConfig, M70LogLevel, M70LogTarget

# Enable debug logging
config = M70LogConfig()
config.level = M70LogLevel.WARNING
config.target = M70LogTarget.CONSOLE
M70Logger.init(config)

conn = M70Connection('192.168.1.206', 683, 6)
if conn.connect():
    print('Connected')
    
    # Try to read program block
    ret, block = conn.read_program_block(1, 10)
    print(f'Result: ret={ret}, block="{block}"')
    
    # Check if main program is running
    ret, main_prog = conn.read_main_program_name(1)
    print(f'Main prog: {main_prog}')
    
    ret, status, mode, run_status = conn.read_status(1)
    print(f'Status: status={status}, mode={mode}, run_status={run_status}')
    
    conn.disconnect()

M70Logger.shutdown()
