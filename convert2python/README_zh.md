# Mitsubishi CNC M70 EZSocket Python Library

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## 📖 目錄

- [概述](#概述)
- [快速開始](#快速開始)
- [完整使用指南](#完整使用指南)
- [API 文檔](#api-文檔)
- [示例代碼](#示例代碼)
- [日誌系統](#日誌系統)
- [故障排除](#故障排除)
- [項目信息](#項目信息)

---

## 概述

這是一個用於通過以太網使用EZSocket協議與三菱CNC M70系列機器通信的Python庫。從原始C語言庫轉換而來，提供完整功能和簡潔的Python API。

**主要特性：**
- ✅ 跨平台支持（Windows/Linux）
- ✅ 完整的EZSocket協議實現
- ✅ 豐富的數據讀取API
- ✅ 純Python實現，無需編譯
- ✅ 無額外依賴，使用標準庫

**支持的CNC型號：**
- 70M
- 80M (待測試)

---

## 快速開始

### 第一步：驗證環境

```bash
cd convert2python
python quick_test.py
```

看到 "✓ 所有測試通過！" 表示可以正常使用。

### 第二步：最簡單的例子

```python
from m70_ezsocket import M70Connection, M70NCType

# 連接到CNC（修改為你的IP地址）
cnc = M70Connection("192.168.123.130", 683, M70NCType.MELDAS700M)

if cnc.connect():
    # 讀取版本
    ret, version = cnc.read_nc_version()
    print(f"CNC版本: {version}")
    
    # 斷開連接
    cnc.disconnect()
```

### 第三步：運行完整示例

```bash
# 修改 examples/simple_example.py 中的IP地址為你的CNC IP
cd examples
python simple_example.py
```

**成功輸出示例：**
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

## 完整使用指南

### 1️⃣ 連接到CNC

```python
from m70_ezsocket import M70Connection, M70NCType, M70ErrorCode

# 創建連接對象
cnc = M70Connection(
    ip="192.168.123.130",      # CNC的IP地址
    port=683,                   # 端口號（通常是683）
    nc_type=M70NCType.MELDAS700M  # CNC型號
)

# 連接
if cnc.connect():
    print("連接成功")
    
    # ... 你的操作 ...
    
    # 記得斷開連接
    cnc.disconnect()
else:
    print("連接失敗")
```

### 2️⃣ 讀取CNC基本信息

```python
# 讀取版本信息
ret, nc_version = cnc.read_nc_version()
ret, nc_name = cnc.read_nc_name_version()
ret, plc_version = cnc.read_plc_version()

# 讀取機器類型
ret, machine_type = cnc.read_nc_type()  # MC 或 LATHE

# 讀取軸數量
ret, nc_axis_count = cnc.read_nc_axis_count()
ret, spindle_count = cnc.read_spindle_axis_count()
ret, all_axis_count = cnc.read_all_axis_count()
```

### 3️⃣ 讀取運行狀態

```python
from m70_ezsocket.typedef import M70DeviceStatus, M70RunMode

# 讀取CNC狀態
ret, status, mode, run_status = cnc.read_status(system_no=1)

if ret == M70ErrorCode.OK:
    print(f"設備狀態: {status}")      # IDLE, RUN, STOP, DEBUG
    print(f"運行模式: {mode}")        # MEM, MDI, JOG, etc.
    print(f"運行狀態: {run_status}")  # RST, EMG, RDY, AUT
```

### 4️⃣ 讀取軸位置

```python
from m70_ezsocket.typedef import PositionType

# 讀取軸名稱
ret, axis_names, axis_count = cnc.read_axis_name(1)
print(f"軸名稱: {axis_names}")  # 例如: "XYZ"

# 讀取所有軸的位置（工件坐標系）
ret, positions = cnc.read_all_axis_position(1, PositionType.POS_WRK)
print(f"工件坐標: {positions}")  # [100.0, 200.0, 50.0]

# 讀取機械坐標
ret, positions = cnc.read_all_axis_position(1, PositionType.POS_MCH)

# 讀取相對坐標
ret, positions = cnc.read_all_axis_position(1, PositionType.POS_RELATV)

# 讀取程序坐標
ret, positions = cnc.read_all_axis_position(1, PositionType.POS_PROGRAM)
```

### 5️⃣ 讀取主軸信息

```python
# 讀取主軸速度
ret, speed = cnc.read_spindle_speed(system_no=1, axis_index=1)
print(f"主軸速度: {speed} RPM")

# 讀取主軸倍率
ret, override = cnc.read_spindle_override(1)
print(f"主軸倍率: {override}%")

# 讀取主軸負載
ret, load = cnc.read_spindle_load(system_no=1, axis_index=1, is_abs=False)
print(f"主軸負載: {load}%")
```

### 6️⃣ 讀取進給信息

```python
from m70_ezsocket.typedef import FeedSpeedType

# 讀取進給速度
ret, speed = cnc.read_feed_speed(1, FeedSpeedType.FC)  # FC: 自動有效進給速度
print(f"進給速度: {speed}")

# 讀取進給倍率
ret, override = cnc.read_feed_override(1)
print(f"進給倍率: {override}%")
```

### 7️⃣ 讀取程序和刀具信息

```python
from m70_ezsocket.typedef import ProgramNameType

# 讀取主程序名稱
ret, main_prog = cnc.read_main_program_name(1, ProgramNameType.PROGRAM_NO)
print(f"主程序: {main_prog}")

# 讀取子程序名稱
ret, sub_prog = cnc.read_sub_program_name(1, ProgramNameType.PROGRAM_NO)

# 讀取當前刀具號
ret, tool_no = cnc.read_current_tool_no(1)
print(f"當前刀具: T{tool_no}")
```

### 8️⃣ 讀取時間信息

```python
# 讀取開機時間（分鐘）
ret, power_time = cnc.read_power_on_time()

# 讀取自動運行時間（分鐘）
ret, auto_time = cnc.read_auto_operation_time()

# 讀取循環時間（秒）
ret, cycle_time = cnc.read_cycle_time()

# 讀取切削時間（秒）
ret, cutting_time = cnc.read_cutting_time()

# 讀取系統日期時間
ret, date, time = cnc.read_system_datetime()
```

---

## API 文檔

### 連接管理

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `M70Connection(ip, port, nc_type)` | 創建連接對象 | 連接對象 |
| `connect()` | 連接到CNC | `bool` |
| `disconnect()` | 斷開連接 | `None` |
| `is_connected()` | 檢查連接狀態 | `bool` |

### 狀態讀取

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `read_status(system_no)` | 讀取CNC狀態 | `(ErrorCode, status, mode, run_status)` |
| `read_nc_version()` | 讀取NC版本 | `(ErrorCode, str)` |
| `read_nc_name_version()` | 讀取NC名稱版本 | `(ErrorCode, str)` |
| `read_plc_version()` | 讀取PLC版本 | `(ErrorCode, str)` |
| `read_nc_type()` | 讀取機器類型 | `(ErrorCode, MachineType)` |
| `read_system_count()` | 讀取系統數量 | `(ErrorCode, int)` |
| `read_nc_axis_count()` | 讀取NC軸數量 | `(ErrorCode, int)` |
| `read_all_axis_count()` | 讀取所有軸數量 | `(ErrorCode, int)` |
| `read_spindle_axis_count()` | 讀取主軸數量 | `(ErrorCode, int)` |

### 位置讀取

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `read_axis_name(system_no)` | 讀取軸名稱 | `(ErrorCode, str, int)` |
| `read_axis_position(system_no, axis_index, pos_type)` | 讀取單軸位置 | `(ErrorCode, float)` |
| `read_all_axis_position(system_no, pos_type)` | 讀取所有軸位置 | `(ErrorCode, List[float])` |

### 主軸信息

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `read_spindle_speed(system_no, axis_index)` | 讀取主軸速度 | `(ErrorCode, int)` |
| `read_spindle_override(system_no)` | 讀取主軸倍率 | `(ErrorCode, int)` |
| `read_spindle_load(system_no, axis_index, is_abs)` | 讀取主軸負載 | `(ErrorCode, int)` |

### 進給信息

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `read_feed_speed(system_no, speed_type)` | 讀取進給速度 | `(ErrorCode, float)` |
| `read_feed_override(system_no)` | 讀取進給倍率 | `(ErrorCode, int)` |

### 程序信息

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `read_main_program_name(system_no, name_type)` | 讀取主程序名 | `(ErrorCode, str)` |
| `read_sub_program_name(system_no, name_type)` | 讀取子程序名 | `(ErrorCode, str)` |
| `read_current_tool_no(system_no)` | 讀取當前刀具號 | `(ErrorCode, int)` |

### 時間信息

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `read_power_on_time()` | 讀取開機時間（分鐘） | `(ErrorCode, int)` |
| `read_auto_operation_time()` | 讀取自動運行時間（分鐘） | `(ErrorCode, int)` |
| `read_cycle_time()` | 讀取循環時間（秒） | `(ErrorCode, int)` |
| `read_cutting_time()` | 讀取切削時間（秒） | `(ErrorCode, int)` |
| `read_system_datetime()` | 讀取系統日期時間 | `(ErrorCode, int, int)` |

---

## 示例代碼

### 示例1：監控CNC狀態

```python
from m70_ezsocket import M70Connection, M70NCType, M70ErrorCode
import time

cnc = M70Connection("192.168.123.130", 683, M70NCType.MELDAS700M)

if cnc.connect():
    print("開始監控CNC狀態...")
    
    try:
        while True:
            # 讀取狀態
            ret, status, mode, run_status = cnc.read_status(1)
            
            # 讀取主軸速度
            ret, speed = cnc.read_spindle_speed(1, 1)
            
            # 讀取進給速度
            ret, feed = cnc.read_feed_speed(1)
            
            print(f"狀態: {status}, 模式: {mode}, 主軸: {speed}RPM, 進給: {feed:.2f}")
            
            time.sleep(1)  # 每秒更新一次
            
    except KeyboardInterrupt:
        print("\n停止監控")
    finally:
        cnc.disconnect()
```

### 示例2：讀取所有軸位置

```python
from m70_ezsocket import M70Connection, M70NCType
from m70_ezsocket.typedef import PositionType

cnc = M70Connection("192.168.123.130", 683, M70NCType.MELDAS700M)

if cnc.connect():
    # 讀取軸名稱
    ret, axis_names, axis_count = cnc.read_axis_name(1)
    print(f"軸名稱: {axis_names}")
    print(f"軸數量: {axis_count}\n")
    
    # 讀取不同坐標系的位置
    pos_types = [
        (PositionType.POS_WRK, "工件坐標"),
        (PositionType.POS_MCH, "機械坐標"),
        (PositionType.POS_RELATV, "相對坐標"),
        (PositionType.POS_PROGRAM, "程序坐標"),
    ]
    
    for pos_type, name in pos_types:
        ret, positions = cnc.read_all_axis_position(1, pos_type)
        print(f"{name}: {positions}")
    
    cnc.disconnect()
```

### 示例3：完整的數據採集

```python
from m70_ezsocket import M70Connection, M70NCType, M70ErrorCode
from m70_ezsocket.typedef import PositionType, FeedSpeedType

def collect_cnc_data(ip: str, port: int = 683):
    """採集CNC所有數據"""
    cnc = M70Connection(ip, port, M70NCType.MELDAS700M)
    
    if not cnc.connect():
        print("連接失敗")
        return None
    
    data = {}
    
    try:
        # 基本信息
        ret, data['version'] = cnc.read_nc_version()
        ret, data['machine_type'] = cnc.read_nc_type()
        
        # 狀態
        ret, status, mode, run_status = cnc.read_status(1)
        data['status'] = {'device': status, 'mode': mode, 'run': run_status}
        
        # 軸信息
        ret, names, count = cnc.read_axis_name(1)
        ret, positions = cnc.read_all_axis_position(1, PositionType.POS_WRK)
        data['axes'] = {'names': names, 'count': count, 'positions': positions}
        
        # 主軸
        ret, speed = cnc.read_spindle_speed(1, 1)
        ret, override = cnc.read_spindle_override(1)
        ret, load = cnc.read_spindle_load(1, 1, False)
        data['spindle'] = {'speed': speed, 'override': override, 'load': load}
        
        # 進給
        ret, feed_speed = cnc.read_feed_speed(1, FeedSpeedType.FC)
        ret, feed_override = cnc.read_feed_override(1)
        data['feed'] = {'speed': feed_speed, 'override': feed_override}
        
        # 刀具
        ret, tool = cnc.read_current_tool_no(1)
        data['tool'] = tool
        
        # 程序
        ret, main_prog = cnc.read_main_program_name(1)
        data['program'] = main_prog
        
        # 時間
        ret, power_time = cnc.read_power_on_time()
        ret, cycle_time = cnc.read_cycle_time()
        data['time'] = {'power_on': power_time, 'cycle': cycle_time}
        
        return data
        
    finally:
        cnc.disconnect()

# 使用
data = collect_cnc_data("192.168.123.130")
if data:
    print("採集的數據:", data)
```

---

## 日誌系統

### 配置日誌

```python
from m70_ezsocket import M70Logger, M70LogConfig, M70LogLevel, M70LogTarget

# 創建配置
config = M70LogConfig()
config.level = M70LogLevel.INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
config.target = M70LogTarget.BOTH        # CONSOLE, FILE, BOTH
config.log_file_path = "./logs/cnc.log"  # 日誌文件路徑
config.include_timestamp = True          # 包含時間戳
config.include_level = True              # 包含日誌級別
config.include_file_line = True          # 包含文件名和行號
config.max_file_size = 10 * 1024 * 1024  # 最大文件大小 10MB
config.max_file_count = 5                # 保留5個歷史文件

# 初始化
M70Logger.init(config)

# 使用
M70Logger.debug("調試信息")
M70Logger.info("一般信息")
M70Logger.warning("警告信息")
M70Logger.error("錯誤信息")
M70Logger.critical("嚴重錯誤")

# 關閉
M70Logger.shutdown()
```

### 日誌級別說明

- **DEBUG**: 詳細的調試信息（開發時使用）
- **INFO**: 一般信息（正常操作）
- **WARNING**: 警告信息（需要注意但不影響運行）
- **ERROR**: 錯誤信息（操作失敗）
- **CRITICAL**: 嚴重錯誤（系統級問題）

---

## 故障排除

### Q1: 連接失敗

**症狀**: `connect()` 返回 `False`

**檢查清單**:
1. ✅ CNC機器是否開機
2. ✅ IP地址是否正確
3. ✅ 端口號是否正確（通常是683）
4. ✅ 網絡是否連通（嘗試 `ping IP地址`）
5. ✅ CNC的以太網模塊是否已配置
6. ✅ 防火牆是否阻擋連接

**解決方案**:
```python
# 測試網絡連通性
import socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex(("192.168.123.130", 683))
    if result == 0:
        print("端口開放")
    else:
        print("端口關閉或無法連接")
    sock.close()
except Exception as e:
    print(f"網絡錯誤: {e}")
```

### Q2: 讀取數據返回錯誤

**症狀**: API返回 `M70ErrorCode.FAILED`

**可能原因**:
- CNC不在正確的狀態
- system_no 參數錯誤
- 該功能在當前CNC型號不支持

**解決方案**:
```python
# 開啟詳細日誌
config = M70LogConfig()
config.level = M70LogLevel.DEBUG
config.target = M70LogTarget.BOTH
M70Logger.init(config)

# 查看日誌文件 logs/mitsubishi_cnc.log
```

### Q3: 數據不更新

**症狀**: 讀取的數據值一直不變

**可能原因**:
- 讀取頻率太快
- CNC狀態未改變

**解決方案**:
```python
import time

# 在讀取之間加入延遲
ret, pos1 = cnc.read_all_axis_position(1, PositionType.POS_WRK)
time.sleep(0.1)  # 延遲100ms
ret, pos2 = cnc.read_all_axis_position(1, PositionType.POS_WRK)
```

### Q4: Python版本問題

**要求**: Python 3.7 或更高版本

**檢查版本**:
```bash
python --version
```

### Q5: 找不到模塊

**症狀**: `ModuleNotFoundError: No module named 'm70_ezsocket'`

**解決方案**:
確保在正確的目錄運行：
```bash
cd convert2python
python examples/simple_example.py
```

或者添加路徑：
```python
import sys
sys.path.insert(0, 'path/to/convert2python')
from m70_ezsocket import M70Connection
```

---

## 項目信息

### 目錄結構

```
convert2python/
├── m70_ezsocket/          # 主庫
│   ├── __init__.py        # 包初始化
│   ├── typedef.py         # 類型定義和枚舉
│   ├── m70_error.py       # 錯誤處理
│   ├── m70_log.py         # 日誌系統
│   ├── m70_socket.py      # Socket通信
│   ├── m70_giop.py        # GIOP協議
│   └── m70_connection.py  # 主連接類
├── examples/              # 示例程序
│   ├── simple_example.py  # 簡單示例
│   └── main.py           # 完整示例
├── logs/                  # 日誌目錄
├── README.md             # 本文檔
├── requirements.txt      # 依賴（無）
├── test_library.py       # 單元測試
├── quick_test.py         # 快速測試
└── .gitignore           # Git配置
```

### 系統要求

- **Python**: 3.7 或更高版本
- **操作系統**: Windows / Linux
- **依賴**: 無（僅使用Python標準庫）
- **硬件**: 三菱CNC M70系列機器，已配置以太網模塊

### 轉換說明

本項目從以下C語言項目轉換而來：
- **原始項目**: https://github.com/wqliceman/mitsubishi_cnc_m70_ezsocket_net
- **轉換日期**: 2025年12月19日
- **轉換內容**: 完整功能，29個主要API
- **代碼行數**: ~3200行（含文檔）

### 功能完成度

✅ **100%** - 所有C語言庫的主要功能已實現
- 連接管理 (3項)
- 狀態讀取 (11項)
- 位置讀取 (3項)
- 主軸信息 (3項)
- 進給信息 (2項)
- 程序信息 (3項)
- 時間信息 (6項)

### 測試狀態

所有基礎測試通過：
```bash
python quick_test.py
```

輸出：
```
✓ 所有模塊導入成功
✓ 連接對象創建成功
✓ 日誌系統正常工作
✓ 所有枚舉定義正確
✓ 所有測試通過！
```

### 許可證

MIT License - 可自由使用、修改和分發

### 貢獻

歡迎提交問題報告和功能建議：
- GitHub Issues: https://github.com/wqliceman/mitsubishi_cnc_m70_ezsocket_net/issues

### 技術支持

- 📖 完整API文檔：見上方 [API文檔](#api-文檔) 章節
- 💻 示例代碼：`examples/` 目錄
- 🔍 日誌文件：`logs/mitsubishi_cnc.log`
- ❓ 常見問題：見上方 [故障排除](#故障排除) 章節

### 版本信息

- **當前版本**: 1.0.0
- **Python版本**: 3.7+
- **協議版本**: GIOP 1.0
- **更新日期**: 2025-12-19

---

## 聯繫方式

如有任何問題或建議，歡迎通過以下方式聯繫：
- GitHub Issues
- Pull Requests

---

**祝使用愉快！ 🎉**
