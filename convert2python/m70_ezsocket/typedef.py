"""
Type definitions and enumerations for M70 EZSocket protocol
Converted from typedef.h
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import List

# Constants
BUFFER_SIZE = 512


class M70ErrorCode(IntEnum):
    """Error codes for M70 operations"""
    OK = 0
    FAILED = 1
    SOCKET_FAILED = 2
    UNKNOWN = 99


class M70NCType(IntEnum):
    """Mitsubishi CNC NC Types"""
    MAGICCARD64 = 0      # MELDASMAGIC Card64
    MAGICBOARD64 = 1     # MELDASMAGIC64
    MELDAS6X5L = 2       # MELDAS600L(M6x5L)
    MELDAS6X5M = 3       # MELDAS600M(M6x5M)
    MELDASC6C64 = 4      # MELDASC6C64
    MELDAS700L = 5       # MELDAS700L
    MELDAS700M = 6       # MELDAS700M
    MELDASC70 = 7        # MELDASC70
    MELDAS800M = 8       # MELDAS800M
    MELDAS800L = 9       # MELDAS800L


class M70DataType(IntEnum):
    """Data types for communication"""
    T_CHAR = 0x1         # 1 byte
    T_SHORT = 0x2        # 2 bytes
    T_LONG = 0x3         # 4 bytes
    T_DLONG = 0x4        # 8 bytes
    T_DOUBLE = 0x5       # 8 bytes
    T_FLOATBIN = 0x6     # 16 bytes
    
    T_STR = 0x10
    T_DecStr = 0x11
    T_HexStr = 0x12
    T_BinStr = 0x13
    T_FloatStr = 0x14
    T_WStr = 0x15
    T_DecWStr = 0x16
    T_HexWStr = 0x17
    T_BinWStr = 0x18
    T_FloatWStr = 0x19
    T_CharBuff = 0x1a
    
    T_UCHAR = 0x21
    T_USHORT = 0x22
    T_UINT32 = 0x23
    
    T_CLCTDATA = 0x100   # 36 bytes
    T_BUFF = 0x103


class M70DeviceStatus(IntEnum):
    """Device status"""
    UNKNOWN = 0
    STOP = 1        # Stop alarm
    RUN = 2         # Running
    IDLE = 3        # Idle
    OFFLINE = 4     # Offline
    DEBUG = 5       # Debugging


class M70RunMode(IntEnum):
    """Run mode of CNC machine"""
    MEM = 0    # Memory mode
    DNC = 1    # RS232(DNC)
    LNK = 2    # Link
    MDI = 3    # MDI mode
    PC = 4     # PC
    MNL = 5    # Manual
    JOG = 6    # Jog
    J_H = 7    # Jog+Handle
    R_H = 8    # R+H
    HDL = 9    # Handle
    STP = 10   # Step
    STP1 = 11  # Step1
    ZRN = 12   # Zero return
    DRT = 13   # Direct
    INI = 14   # Initial
    NON = 15   # None
    LIN = 16   # Link


class M70RunStatus(IntEnum):
    """Running status"""
    RST = 0    # Reset
    EMG = 1    # Emergency
    RDY = 2    # Ready
    AUT = 3    # Auto
    SYN = 4    # Sync
    CRS = 5    # Cross
    BST = 6    # Burst
    HLD = 7    # Hold


class M70NCMachineType(IntEnum):
    """NC Machine Type"""
    MC = 0       # Machining Center
    LATHE = 1    # Lathe


class M70CommonVariableType(IntEnum):
    """Common variable types"""
    VAR_TYPE_100 = 0
    VAR_TYPE_500 = 1


class ProgramNameType(IntEnum):
    """Program name types"""
    PROGRAM_NO = 0
    SEQUENCE_NUMBER = 1
    BLOCK_NUMBER = 2
    PROGRAM_PATH = 3


class M70FileInfoType(IntEnum):
    """File information types"""
    REG_PROG_NOS = 0      # Number of registered machining programs
    USED_PROG_NOS = 1     # Remaining machining programs
    CAPA_CHAR_NOS = 2     # Machining program character capacity
    FREE_CHAR_NOS = 3     # Remaining characters in machining program
    TRANS_SIZE = 4        # Transfer data size for melCopyFile


class PositionType(IntEnum):
    """Position types"""
    POS_WRK = 0         # Workpiece coordinate position counter
    POS_MCH = 1         # Machine position counter
    POS_CURRENT = 2     # Current position counter
    POS_RELATV = 3      # Relative position counter
    POS_PROGRAM = 4     # Program position counter
    DISTANCE = 5        # Remaining command


class FeedSpeedType(IntEnum):
    """Feed speed types"""
    FA = 0    # F command feed rate (FA)
    FM = 1    # Manual effective feed rate (FM)
    FS = 2    # Synchronous feed rate (FS)
    FC = 3    # Automatic effective feed rate (Fc)
    FE = 4    # Screw feed (FE)


class PLCDataType(IntEnum):
    """PLC data types"""
    BIT = 0
    CHAR = 1
    SHORT = 2
    INT32 = 3
    DLONG = 4
    DOUBLE = 5


class AlarmMessageType(IntEnum):
    """Alarm message types"""
    ALL_ALARM = 0x000
    NC_ALARM = 0x100
    STOP_CODE = 0x200
    PLC_ALARM = 0x300
    OPE_MSG = 0x400
    ALL_NON_STOPCD = 0x1000
    NC_SYSTEM = 0x101
    NC_SERVO = 0x102
    NC_MCP = 0x103
    NC_BASICPLC = 0x104
    NC_USERPLC = 0x105
    NC_PROGRAM = 0x106
    NC_SERVO_WARNING = 0x107
    NC_MCP_WARNING = 0x108
    NC_SYSTEM_WARNING = 0x109
    NC_OPERATION = 0x10A
    OPE_ALARM = 0x10B


@dataclass
class M70Connection:
    """Connection information"""
    socket: int = -1
    connected: bool = False
    nc_type: M70NCType = M70NCType.MELDAS700M
    request_id: int = 0
    little_endian: bool = True


@dataclass
class ProgBlock:
    """Program block information"""
    block_length: int = 0
    text: str = ""


@dataclass
class AlarmString:
    """Alarm string information"""
    alarm_length: int = 0
    messages: List[str] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


@dataclass
class FileFSStat:
    """File status information"""
    size: int = 0
    date: int = 0
    time: int = 0
    attribute: int = 0
