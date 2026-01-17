using System.Runtime.InteropServices;

namespace MitsubishiCncM70;

/// <summary>
/// Error codes for M70 operations
/// </summary>
public enum M70ErrorCode
{
    OK = 0,
    Failed = 1,
    SocketFailed = 2,
    Unknown = 99
}

/// <summary>
/// CNC System Types
/// </summary>
public enum M70NCType
{
    MagicCard64 = 0,
    MagicBoard64 = 1,
    Meldas6X5L = 2,
    Meldas6X5M = 3,
    MeldasC6C64 = 4,
    Meldas700L = 5,
    Meldas700M = 6,
    MeldasC70 = 7,
    Meldas800M = 8,
    Meldas800L = 9
}

/// <summary>
/// Data types for GIOP protocol
/// </summary>
public enum M70DataType
{
    Char = 0x1,
    Short = 0x2,
    Long = 0x3,
    DLong = 0x4,
    Double = 0x5,
    FloatBin = 0x6,

    Str = 0x10,
    DecStr = 0x11,
    HexStr = 0x12,
    BinStr = 0x13,
    FloatStr = 0x14,
    WStr = 0x15,
    DecWStr = 0x16,
    HexWStr = 0x17,
    BinWStr = 0x18,
    FloatWStr = 0x19,
    CharBuff = 0x1a,

    UChar = 0x21,
    UShort = 0x22,
    UInt32 = 0x23,

    ClctData = 0x100,
    Buff = 0x103
}

/// <summary>
/// Device status
/// </summary>
public enum M70DeviceStatus
{
    Unknown = 0,
    Stop = 1,
    Run = 2,
    Idle = 3,
    Offline = 4,
    Debug = 5
}

/// <summary>
/// Run mode
/// </summary>
public enum M70RunMode
{
    MEM = 0,
    DNC = 1,
    LNK = 2,
    MDI = 3,
    PC = 4,
    MNL = 5,
    JOG = 6,
    J_H = 7,
    R_H = 8,
    HDL = 9,
    STP = 10,
    STP1 = 11,
    ZRN = 12,
    DRT = 13,
    INI = 14,
    NON = 15,
    LIN = 16
}

/// <summary>
/// Run status
/// </summary>
public enum M70RunStatus
{
    RST = 0,
    EMG = 1,
    RDY = 2,
    AUT = 3,
    SYN = 4,
    CRS = 5,
    BST = 6,
    HLD = 7
}

/// <summary>
/// NC machine type
/// </summary>
public enum M70NCMachineType
{
    MC = 0,
    Lathe = 1
}

/// <summary>
/// Program name type
/// </summary>
public enum ProgramNameType
{
    ProgramNo = 0,
    SequenceNumber = 1,
    BlockNumber = 2,
    ProgramPath = 3
}

/// <summary>
/// File info type
/// </summary>
public enum M70FileInfoType
{
    RegProgNos = 0,
    UsedProgNos = 1,
    CapaCharNos = 2,
    FreeCharNos = 3,
    TransSize = 4
}

/// <summary>
/// Position type
/// </summary>
public enum PositionType
{
    WRK = 0,
    MCH = 1,
    Current = 2,
    Relatv = 3,
    Program = 4,
    Distance = 5
}

/// <summary>
/// Feed speed type
/// </summary>
public enum FeedSpeedType
{
    FA = 0,
    FM = 1,
    FS = 2,
    FC = 3,
    FE = 4
}

/// <summary>
/// Alarm message type
/// </summary>
public enum AlarmType
{
    AllAlarm = 0x000,
    NCAlarm = 0x100,
    StopCode = 0x200,
    PLCAlarm = 0x300,
    OpeMsg = 0x400,
    AllNonStopCd = 0x1000,
    NCSystem = 0x101,
    NCServo = 0x102,
    NCMCP = 0x103,
    NCBasicPLC = 0x104,
    NCUserPLC = 0x105,
    NCProgram = 0x106,
    NCServoWarning = 0x107,
    NCMCPWarning = 0x108,
    NCSystemWarning = 0x109,
    NCOperation = 0x10A,
    OpeAlarm = 0x10B
}

/// <summary>
/// Alarm message structure
/// </summary>
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct AlarmString
{
    public int AlarmNo;
    public int AlarmLength;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 256)]
    public byte[] Text;

    public string GetText()
    {
        if (Text == null || AlarmLength <= 0) return string.Empty;
        return System.Text.Encoding.UTF8.GetString(Text, 0, Math.Min(AlarmLength, 256));
    }
}

/// <summary>
/// Program block structure
/// </summary>
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ProgBlock
{
    public int CurrentBlock;
    public int CurrentRow;
    public int U1;
    public int BlockLength;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 512)]
    public byte[] Text;

    public string GetText()
    {
        if (Text == null || BlockLength <= 0) return string.Empty;
        return System.Text.Encoding.UTF8.GetString(Text, 0, Math.Min(BlockLength, 512));
    }
}

/// <summary>
/// File stat information
/// </summary>
public class FileStatInfo
{
    public uint Mode { get; set; }
    public ulong FileSize { get; set; }
    public ushort Year { get; set; }
    public ushort Month { get; set; }
    public ushort Day { get; set; }
    public ushort Hour { get; set; }
    public ushort Minute { get; set; }
    public ushort Second { get; set; }
}
