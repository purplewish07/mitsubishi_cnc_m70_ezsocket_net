# Mitsubishi CNC M70 EZSocket Python Library

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**[中文文檔 (Chinese Documentation)](README_zh.md)**

---

## 📖 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Complete Usage Guide](#complete-usage-guide)
- [API Documentation](#api-documentation)
- [Example Code](#example-code)
- [Logging System](#logging-system)
- [Troubleshooting](#troubleshooting)
- [Project Information](#project-information)

---

## Overview

This is a Python library for communicating with Mitsubishi CNC M70 series machines over Ethernet using the EZSocket protocol. Converted from the original C library, it provides complete functionality with a clean Python API.

**Key Features:**
- ✅ Cross-platform support (Windows/Linux)
- ✅ Complete EZSocket protocol implementation
- ✅ Rich data reading APIs
- ✅ Pure Python implementation, no compilation required
- ✅ No external dependencies, uses only standard library

**Supported CNC Models:**
- 70M
- 80M (wait for test)

---

## Quick Start

### Step 1: Verify Environment

```bash
cd convert2python
python quick_test.py
```

You should see "✓ All tests passed!" indicating the library is ready to use.

### Step 2: Simplest Example

```python
from m70_ezsocket import M70Connection, M70NCType

# Connect to CNC (change to your IP address)
cnc = M70Connection("192.168.123.130", 683, M70NCType.MELDAS700M)

if cnc.connect():
    # Read version
    ret, version = cnc.read_nc_version()
    print(f"CNC Version: {version}")
    
    # Disconnect
    cnc.disconnect()
```

### Step 3: Run Full Example

```bash
# Edit examples/simple_example.py and change the IP to your CNC IP
cd examples
python simple_example.py
```

**Expected Output:**
```
Connected successfully!
CNC Version: M70 V1.xx
Status: DeviceStatus.IDLE, Mode: RunMode.MEM
Axis Names: XYZ (Count: 3)
Axis Positions: [0.0, 0.0, 0.0]
Spindle Speed: 0 RPM
Current Tool: T1
```

---

## Complete Usage Guide

### 1️⃣ Connect to CNC

```python
from m70_ezsocket import M70Connection, M70NCType, M70ErrorCode

# Create connection object
cnc = M70Connection(
    ip="192.168.123.130",      # CNC IP address
    port=683,                   # Port number (usually 683)
    nc_type=M70NCType.MELDAS700M  # CNC model
)

# Connect
if cnc.connect():
    print("Connected successfully")
    
    # ... your operations ...
    
    # Remember to disconnect
    cnc.disconnect()
else:
    print("Connection failed")
```

### 2️⃣ Read CNC Basic Information

```python
# Read version information
ret, nc_version = cnc.read_nc_version()
ret, nc_name = cnc.read_nc_name_version()
ret, plc_version = cnc.read_plc_version()

# Read machine type
ret, machine_type = cnc.read_nc_type()  # MC or LATHE

# Read axis counts
ret, nc_axis_count = cnc.read_nc_axis_count()
ret, spindle_count = cnc.read_spindle_axis_count()
ret, all_axis_count = cnc.read_all_axis_count()
```

### 3️⃣ Read Running Status

```python
from m70_ezsocket.typedef import M70DeviceStatus, M70RunMode

# Read CNC status
ret, status, mode, run_status = cnc.read_status(system_no=1)

if ret == M70ErrorCode.OK:
    print(f"Device Status: {status}")    # IDLE, RUN, STOP, DEBUG
    print(f"Run Mode: {mode}")           # MEM, MDI, JOG, etc.
    print(f"Run Status: {run_status}")   # RST, EMG, RDY, AUT
```

### 4️⃣ Read Axis Positions

```python
from m70_ezsocket.typedef import PositionType

# Read axis names
ret, axis_names, axis_count = cnc.read_axis_name(1)
print(f"Axis Names: {axis_names}")  # e.g., "XYZ"

# Read all axis positions (workpiece coordinate system)
ret, positions = cnc.read_all_axis_position(1, PositionType.POS_WRK)
print(f"Workpiece Coordinates: {positions}")  # [100.0, 200.0, 50.0]

# Read machine coordinates
ret, positions = cnc.read_all_axis_position(1, PositionType.POS_MCH)

# Read relative coordinates
ret, positions = cnc.read_all_axis_position(1, PositionType.POS_RELATV)

# Read program coordinates
ret, positions = cnc.read_all_axis_position(1, PositionType.POS_PROGRAM)
```

### 5️⃣ Read Spindle Information

```python
# Read spindle speed
ret, speed = cnc.read_spindle_speed(system_no=1, axis_index=1)
print(f"Spindle Speed: {speed} RPM")

# Read spindle override
ret, override = cnc.read_spindle_override(1)
print(f"Spindle Override: {override}%")

# Read spindle load
ret, load = cnc.read_spindle_load(system_no=1, axis_index=1, is_abs=False)
print(f"Spindle Load: {load}%")
```

### 6️⃣ Read Feed Information

```python
from m70_ezsocket.typedef import FeedSpeedType

# Read feed speed
ret, speed = cnc.read_feed_speed(1, FeedSpeedType.FC)  # FC: Automatic effective feed rate
print(f"Feed Speed: {speed}")

# Read feed override
ret, override = cnc.read_feed_override(1)
print(f"Feed Override: {override}%")
```

### 7️⃣ Read Program and Tool Information

```python
from m70_ezsocket.typedef import ProgramNameType

# Read main program name
ret, main_prog = cnc.read_main_program_name(1, ProgramNameType.PROGRAM_NO)
print(f"Main Program: {main_prog}")

# Read sub program name
ret, sub_prog = cnc.read_sub_program_name(1, ProgramNameType.PROGRAM_NO)

# Read current tool number
ret, tool_no = cnc.read_current_tool_no(1)
print(f"Current Tool: T{tool_no}")
```

### 8️⃣ Read Time Information

```python
# Read power-on time (minutes)
ret, power_time = cnc.read_power_on_time()

# Read auto operation time (minutes)
ret, auto_time = cnc.read_auto_operation_time()

# Read cycle time (seconds)
ret, cycle_time = cnc.read_cycle_time()

# Read cutting time (seconds)
ret, cutting_time = cnc.read_cutting_time()

# Read system date and time
ret, date, time = cnc.read_system_datetime()
```

---

## API Documentation

### Connection Management

| Method | Description | Return Value |
|--------|-------------|--------------|
| `M70Connection(ip, port, nc_type)` | Create connection object | Connection object |
| `connect()` | Connect to CNC | `bool` |
| `disconnect()` | Disconnect from CNC | `None` |
| `is_connected()` | Check connection status | `bool` |

### Status Reading

| Method | Description | Return Value |
|--------|-------------|--------------|
| `read_status(system_no)` | Read CNC status | `(ErrorCode, status, mode, run_status)` |
| `read_nc_version()` | Read NC version | `(ErrorCode, str)` |
| `read_nc_name_version()` | Read NC name version | `(ErrorCode, str)` |
| `read_plc_version()` | Read PLC version | `(ErrorCode, str)` |
| `read_nc_type()` | Read machine type | `(ErrorCode, MachineType)` |
| `read_system_count()` | Read system count | `(ErrorCode, int)` |
| `read_nc_axis_count()` | Read NC axis count | `(ErrorCode, int)` |
| `read_all_axis_count()` | Read all axis count | `(ErrorCode, int)` |
| `read_spindle_axis_count()` | Read spindle count | `(ErrorCode, int)` |

### Position Reading

| Method | Description | Return Value |
|--------|-------------|--------------|
| `read_axis_name(system_no)` | Read axis names | `(ErrorCode, str, int)` |
| `read_axis_position(system_no, axis_index, pos_type)` | Read single axis position | `(ErrorCode, float)` |
| `read_all_axis_position(system_no, pos_type)` | Read all axes positions | `(ErrorCode, List[float])` |

### Spindle Information

| Method | Description | Return Value |
|--------|-------------|--------------|
| `read_spindle_speed(system_no, axis_index)` | Read spindle speed | `(ErrorCode, int)` |
| `read_spindle_override(system_no)` | Read spindle override | `(ErrorCode, int)` |
| `read_spindle_load(system_no, axis_index, is_abs)` | Read spindle load | `(ErrorCode, int)` |

### Feed Information

| Method | Description | Return Value |
|--------|-------------|--------------|
| `read_feed_speed(system_no, speed_type)` | Read feed speed | `(ErrorCode, float)` |
| `read_feed_override(system_no)` | Read feed override | `(ErrorCode, int)` |

### Program Information

| Method | Description | Return Value |
|--------|-------------|--------------|
| `read_main_program_name(system_no, name_type)` | Read main program name | `(ErrorCode, str)` |
| `read_sub_program_name(system_no, name_type)` | Read sub program name | `(ErrorCode, str)` |
| `read_current_tool_no(system_no)` | Read current tool number | `(ErrorCode, int)` |

### Time Information

| Method | Description | Return Value |
|--------|-------------|--------------|
| `read_power_on_time()` | Read power-on time (minutes) | `(ErrorCode, int)` |
| `read_auto_operation_time()` | Read auto operation time (minutes) | `(ErrorCode, int)` |
| `read_cycle_time()` | Read cycle time (seconds) | `(ErrorCode, int)` |
| `read_cutting_time()` | Read cutting time (seconds) | `(ErrorCode, int)` |
| `read_system_datetime()` | Read system date and time | `(ErrorCode, int, int)` |

---

## Example Code

### Example 1: Monitor CNC Status

```python
from m70_ezsocket import M70Connection, M70NCType, M70ErrorCode
import time

cnc = M70Connection("192.168.123.130", 683, M70NCType.MELDAS700M)

if cnc.connect():
    print("Starting CNC status monitoring...")
    
    try:
        while True:
            # Read status
            ret, status, mode, run_status = cnc.read_status(1)
            
            # Read spindle speed
            ret, speed = cnc.read_spindle_speed(1, 1)
            
            # Read feed speed
            ret, feed = cnc.read_feed_speed(1)
            
            print(f"Status: {status}, Mode: {mode}, Spindle: {speed}RPM, Feed: {feed:.2f}")
            
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
    finally:
        cnc.disconnect()
```

### Example 2: Read All Axis Positions

```python
from m70_ezsocket import M70Connection, M70NCType
from m70_ezsocket.typedef import PositionType

cnc = M70Connection("192.168.123.130", 683, M70NCType.MELDAS700M)

if cnc.connect():
    # Read axis names
    ret, axis_names, axis_count = cnc.read_axis_name(1)
    print(f"Axis Names: {axis_names}")
    print(f"Axis Count: {axis_count}\n")
    
    # Read positions in different coordinate systems
    pos_types = [
        (PositionType.POS_WRK, "Workpiece Coordinates"),
        (PositionType.POS_MCH, "Machine Coordinates"),
        (PositionType.POS_RELATV, "Relative Coordinates"),
        (PositionType.POS_PROGRAM, "Program Coordinates"),
    ]
    
    for pos_type, name in pos_types:
        ret, positions = cnc.read_all_axis_position(1, pos_type)
        print(f"{name}: {positions}")
    
    cnc.disconnect()
```

### Example 3: Complete Data Collection

```python
from m70_ezsocket import M70Connection, M70NCType, M70ErrorCode
from m70_ezsocket.typedef import PositionType, FeedSpeedType

def collect_cnc_data(ip: str, port: int = 683):
    """Collect all CNC data"""
    cnc = M70Connection(ip, port, M70NCType.MELDAS700M)
    
    if not cnc.connect():
        print("Connection failed")
        return None
    
    data = {}
    
    try:
        # Basic information
        ret, data['version'] = cnc.read_nc_version()
        ret, data['machine_type'] = cnc.read_nc_type()
        
        # Status
        ret, status, mode, run_status = cnc.read_status(1)
        data['status'] = {'device': status, 'mode': mode, 'run': run_status}
        
        # Axis information
        ret, names, count = cnc.read_axis_name(1)
        ret, positions = cnc.read_all_axis_position(1, PositionType.POS_WRK)
        data['axes'] = {'names': names, 'count': count, 'positions': positions}
        
        # Spindle
        ret, speed = cnc.read_spindle_speed(1, 1)
        ret, override = cnc.read_spindle_override(1)
        ret, load = cnc.read_spindle_load(1, 1, False)
        data['spindle'] = {'speed': speed, 'override': override, 'load': load}
        
        # Feed
        ret, feed_speed = cnc.read_feed_speed(1, FeedSpeedType.FC)
        ret, feed_override = cnc.read_feed_override(1)
        data['feed'] = {'speed': feed_speed, 'override': feed_override}
        
        # Tool
        ret, tool = cnc.read_current_tool_no(1)
        data['tool'] = tool
        
        # Program
        ret, main_prog = cnc.read_main_program_name(1)
        data['program'] = main_prog
        
        # Time
        ret, power_time = cnc.read_power_on_time()
        ret, cycle_time = cnc.read_cycle_time()
        data['time'] = {'power_on': power_time, 'cycle': cycle_time}
        
        return data
        
    finally:
        cnc.disconnect()

# Usage
data = collect_cnc_data("192.168.123.130")
if data:
    print("Collected data:", data)
```

---

## Logging System

### Configure Logging

```python
from m70_ezsocket import M70Logger, M70LogConfig, M70LogLevel, M70LogTarget

# Create configuration
config = M70LogConfig()
config.level = M70LogLevel.INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
config.target = M70LogTarget.BOTH        # CONSOLE, FILE, BOTH
config.log_file_path = "./logs/cnc.log"  # Log file path
config.include_timestamp = True          # Include timestamp
config.include_level = True              # Include log level
config.include_file_line = True          # Include file name and line number
config.max_file_size = 10 * 1024 * 1024  # Max file size 10MB
config.max_file_count = 5                # Keep 5 history files

# Initialize
M70Logger.init(config)

# Usage
M70Logger.debug("Debug information")
M70Logger.info("General information")
M70Logger.warning("Warning information")
M70Logger.error("Error information")
M70Logger.critical("Critical error")

# Shutdown
M70Logger.shutdown()
```

### Log Levels

- **DEBUG**: Detailed debug information (for development)
- **INFO**: General information (normal operations)
- **WARNING**: Warning messages (needs attention but doesn't affect operation)
- **ERROR**: Error messages (operation failed)
- **CRITICAL**: Critical errors (system-level issues)

---

## Troubleshooting

### Q1: Connection Failed

**Symptoms**: `connect()` returns `False`

**Checklist**:
1. ✅ Is the CNC machine powered on?
2. ✅ Is the IP address correct?
3. ✅ Is the port number correct (usually 683)?
4. ✅ Is the network connected (try `ping IP_ADDRESS`)?
5. ✅ Is the CNC's Ethernet module configured?
6. ✅ Is the firewall blocking the connection?

**Solution**:
```python
# Test network connectivity
import socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex(("192.168.123.130", 683))
    if result == 0:
        print("Port is open")
    else:
        print("Port is closed or unreachable")
    sock.close()
except Exception as e:
    print(f"Network error: {e}")
```

### Q2: Reading Data Returns Error

**Symptoms**: API returns `M70ErrorCode.FAILED`

**Possible Causes**:
- CNC is not in the correct state
- system_no parameter is incorrect
- Feature not supported on current CNC model

**Solution**:
```python
# Enable detailed logging
config = M70LogConfig()
config.level = M70LogLevel.DEBUG
config.target = M70LogTarget.BOTH
M70Logger.init(config)

# Check log file logs/mitsubishi_cnc.log
```

### Q3: Data Not Updating

**Symptoms**: Read data values remain constant

**Possible Causes**:
- Reading frequency too high
- CNC state hasn't changed

**Solution**:
```python
import time

# Add delay between reads
ret, pos1 = cnc.read_all_axis_position(1, PositionType.POS_WRK)
time.sleep(0.1)  # Delay 100ms
ret, pos2 = cnc.read_all_axis_position(1, PositionType.POS_WRK)
```

### Q4: Python Version Issue

**Requirement**: Python 3.7 or higher

**Check version**:
```bash
python --version
```

### Q5: Module Not Found

**Symptoms**: `ModuleNotFoundError: No module named 'm70_ezsocket'`

**Solution**:
Make sure you're running from the correct directory:
```bash
cd convert2python
python examples/simple_example.py
```

Or add the path:
```python
import sys
sys.path.insert(0, 'path/to/convert2python')
from m70_ezsocket import M70Connection
```

---

## Project Information

### Directory Structure

```
convert2python/
├── m70_ezsocket/          # Main library
│   ├── __init__.py        # Package initialization
│   ├── typedef.py         # Type definitions and enums
│   ├── m70_error.py       # Error handling
│   ├── m70_log.py         # Logging system
│   ├── m70_socket.py      # Socket communication
│   ├── m70_giop.py        # GIOP protocol
│   └── m70_connection.py  # Main connection class
├── examples/              # Example programs
│   ├── simple_example.py  # Simple example
│   └── main.py           # Full example
├── logs/                  # Log directory
├── README.md             # This document (English)
├── README_zh.md          # Chinese documentation
├── requirements.txt      # Dependencies (none)
├── test_library.py       # Unit tests
├── quick_test.py         # Quick test
└── .gitignore           # Git configuration
```

### System Requirements

- **Python**: 3.7 or higher
- **OS**: Windows / Linux
- **Dependencies**: None (uses only Python standard library)
- **Hardware**: Mitsubishi CNC M70 series machine with configured Ethernet module

### Conversion Notes

This project was converted from the following C project:
- **Original Project**: https://github.com/wqliceman/mitsubishi_cnc_m70_ezsocket_net
- **Conversion Date**: December 19, 2025
- **Conversion Content**: Full functionality, 29 main APIs
- **Lines of Code**: ~3200 lines (including documentation)

### Feature Completeness

✅ **100%** - All main features of the C library implemented
- Connection Management (3 items)
- Status Reading (11 items)
- Position Reading (3 items)
- Spindle Information (3 items)
- Feed Information (2 items)
- Program Information (3 items)
- Time Information (6 items)

### Test Status

All basic tests passed:
```bash
python quick_test.py
```

Output:
```
✓ All modules imported successfully
✓ Connection object created successfully
✓ Logging system works correctly
✓ All enum definitions correct
✓ All tests passed!
```

### License

MIT License - Free to use, modify, and distribute

### Contributing

Issues and feature suggestions are welcome:
- GitHub Issues: https://github.com/wqliceman/mitsubishi_cnc_m70_ezsocket_net/issues

### Technical Support

- 📖 Complete API Documentation: See [API Documentation](#api-documentation) section above
- 💻 Example Code: `examples/` directory
- 🔍 Log Files: `logs/mitsubishi_cnc.log`
- ❓ FAQ: See [Troubleshooting](#troubleshooting) section above

### Version Information

- **Current Version**: 1.0.0
- **Python Version**: 3.7+
- **Protocol Version**: GIOP 1.0
- **Last Updated**: 2025-12-19

---

## Contact

For any questions or suggestions, feel free to contact via:
- GitHub Issues
- Pull Requests

---

**Happy coding! 🎉**
