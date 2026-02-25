using System.Text;

namespace MitsubishiCncM70;

/// <summary>
/// M70 GIOP Protocol Handler
/// Handles low-level GIOP (General Inter-ORB Protocol) communication
/// </summary>
public static class M70GIOP
{
    private const int BufferSize = 512;
    
    // GIOP magic number
    private static readonly byte[] GiopMagic = { (byte)'G', (byte)'I', (byte)'O', (byte)'P' };
    
    // Operation commands
    private const string OpGetData = "mochaGetData";
    private const string OpSetData = "mochaSetData";
    private const string OpGetAlarmMsg = "mochaGetCurrentAlarmMsgFirst";
    private const string OpGetProgBlock = "mochaGetCurrentPrgBlockFirst";
    private const string OpFsOpenFile = "mochaFSOpenFile";
    private const string OpFsReadFile = "mochaFSReadFile";
    private const string OpFsCloseFile = "mochaFSCloseFile";
    private const string OpFsCreateFile = "mochaFSCreateFile";
    private const string OpFsRemoveFile = "mochaFSRemoveFile";
    private const string OpFsWriteFile = "mochaFSWriteFile";
    private const string OpFsStatFile = "mochaFSStatFile";
    private const string OpFsOpenDir = "mochaFSOpenDirectory";
    private const string OpFsCloseDir = "mochaFSCloseDirectory";
    private const string OpFsReadDir = "mochaFSReadDirectory";
    private const string OpFsGetDriveInfo = "mochaFSGetDriveInformation";

    /// <summary>
    /// Get data type length in bytes
    /// </summary>
    public static int GetDataTypeLength(M70DataType dataType)
    {
        return dataType switch
        {
            M70DataType.Char or M70DataType.UChar => 1,
            M70DataType.Short or M70DataType.UShort => 2,
            M70DataType.Long or M70DataType.UInt32 => 4,
            M70DataType.DLong => 8,
            M70DataType.Double => 8,
            M70DataType.FloatBin => 16,
            M70DataType.ClctData => 36,
            _ => 1
        };
    }

    /// <summary>
    /// Build GIOP header
    /// </summary>
    private static byte[] BuildGiopHeader(M70Connection conn, int dataLength)
    {
        using var ms = new MemoryStream();
        using var writer = new BinaryWriter(ms);

        // Magic: "GIOP"
        writer.Write(GiopMagic);
        
        // Version: 1.0
        writer.Write((ushort)1);
        
        // Byte order: 1 = little endian
        writer.Write((byte)(conn.IsLittleEndian ? 1 : 0));
        
        // Message type: 0 = Request
        writer.Write((byte)0);
        
        // Data length
        writer.Write(dataLength);

        return ms.ToArray();
    }

    /// <summary>
    /// Build request header
    /// </summary>
    private static byte[] BuildRequestHeader(M70Connection conn, int opNameLength)
    {
        using var ms = new MemoryStream();
        using var writer = new BinaryWriter(ms);

        // sc_list (4 bytes)
        writer.Write((uint)0);
        
        // Request ID (4 bytes) - DON'T increment, stays constant like Python
        writer.Write((uint)conn.RequestId);
        
        // Response expected: 1 (1 byte)
        writer.Write((byte)1);
        
        // Reserved (3 bytes)
        writer.Write((byte)0);
        writer.Write((byte)0);
        writer.Write((byte)0);
        
        // Object key length (4 bytes)
        writer.Write((uint)4);
        
        // Object key (4 bytes)
        writer.Write((uint)1);
        
        // Operation name length (4 bytes)
        writer.Write((uint)opNameLength);

        return ms.ToArray();
    }

    /// <summary>
    /// Receive response header
    /// </summary>
    private static (int errorCode, int dataLength) ReceiveResponse(M70Connection conn)
    {
        // Read GIOP header (12 bytes)
        var header = conn.ReceiveData(12);
        if (header == null || header.Length != 12)
            return (-1, 0);

        // Check magic
        if (header[0] != 'G' || header[1] != 'I' || header[2] != 'O' || header[3] != 'P')
            return (-1, 0);

        // Get data length
        int dataLength = BitConverter.ToInt32(header, 8);

        // Read response header (12 bytes) - sc_list + request_id + is_error
        var respHeader = conn.ReceiveData(12);
        if (respHeader == null || respHeader.Length != 12)
            return (-1, 0);

        int scList = BitConverter.ToInt32(respHeader, 0);
        int requestId = BitConverter.ToInt32(respHeader, 4);
        int isError = BitConverter.ToInt32(respHeader, 8);
        
        // Calculate remaining length after response header
        int remaining = dataLength - 12;
        
        // If error response
        if (isError != 0)
        {
            // Read and parse error response
            if (remaining >= 4)
            {
                var exceptionLenData = conn.ReceiveData(4);
                if (exceptionLenData != null)
                {
                    int exceptionLen = BitConverter.ToInt32(exceptionLenData, 0);
                    remaining -= 4;
                    
                    // Skip exception string
                    if (exceptionLen > 0 && remaining >= exceptionLen)
                    {
                        conn.ReceiveData(exceptionLen);
                        remaining -= exceptionLen;
                    }
                }
            }
            
            // Read error code structure (11 bytes)
            if (remaining >= 11)
            {
                var errorPack = conn.ReceiveData(11);
                if (errorPack != null && errorPack.Length >= 11)
                {
                    // Error code is at offset 3 (4 bytes)
                    int errorCode = BitConverter.ToInt32(errorPack, 3);
                    return (errorCode, 0);
                }
            }
            return (-1, 0);
        }

        return (0, remaining);
    }

    /// <summary>
    /// Open file on CNC
    /// </summary>
    public static (int errorCode, int fd) MelFsOpenFile(M70Connection conn, string filename, int mode)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (16 bytes)
            var opField = new byte[16];
            var opBytes = Encoding.ASCII.GetBytes(OpFsOpenFile + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 16));
            writer.Write(opField);

            // Build request parameters
            writer.Write((uint)0);   // principal
            writer.Write((uint)0);   // mode (always 0)
            writer.Write((uint)mode); // flag
            writer.Write((uint)filename.Length); // filename length
            writer.Write(Encoding.ASCII.GetBytes(filename));

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x10);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return (-1, 0);

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            if (errorCode != 0)
                return (errorCode, 0);

            int fd = 0;

            // Read return value (4 bytes)
            if (remainingLength >= 4)
            {
                var retData = conn.ReceiveData(4);
                if (retData == null || retData.Length != 4)
                    return (-1, 0);
                remainingLength -= 4;
            }

            // Read file descriptor (4 bytes)
            if (remainingLength >= 4)
            {
                var fdData = conn.ReceiveData(4);
                if (fdData == null || fdData.Length != 4)
                    return (-1, 0);
                fd = BitConverter.ToInt32(fdData, 0);
                remainingLength -= 4;
            }

            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }

            return (0, fd);
        }
        catch
        {
            return (-1, 0);
        }
    }

    /// <summary>
    /// Read file data
    /// </summary>
    public static (int errorCode, int actualSize, byte[]? data) MelFsReadFile(M70Connection conn, int fd, int needReadSize)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (16 bytes)
            var opField = new byte[16];
            var opBytes = Encoding.ASCII.GetBytes(OpFsReadFile + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 16));
            writer.Write(opField);

            // Build request parameters
            writer.Write((uint)0); // principal
            writer.Write(fd);      // file handle
            writer.Write(needReadSize); // read size

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x10);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return (-1, 0, null);

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            if (errorCode != 0)
                return (errorCode, 0, null);

            int actualSize = 0;
            byte[]? fileData = null;

            // Read return value (4 bytes)
            if (remainingLength >= 4)
            {
                var retData = conn.ReceiveData(4);
                if (retData == null || retData.Length != 4)
                    return (-1, 0, null);
                remainingLength -= 4;
            }

            // Read actual read size (4 bytes)
            if (remainingLength >= 4)
            {
                var sizeData = conn.ReceiveData(4);
                if (sizeData == null || sizeData.Length != 4)
                    return (-1, 0, null);
                actualSize = BitConverter.ToInt32(sizeData, 0);
                remainingLength -= 4;
            }

            // Read file data
            if (actualSize > 0 && remainingLength > 0)
            {
                int bytesToRead = Math.Min(actualSize, remainingLength);
                fileData = conn.ReceiveData(bytesToRead);
                remainingLength -= bytesToRead;
            }

            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }

            return (0, actualSize, fileData);
        }
        catch
        {
            return (-1, 0, null);
        }
    }

    /// <summary>
    /// Close file
    /// </summary>
    public static int MelFsCloseFile(M70Connection conn, int fd)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (17 bytes) + 3 reserved bytes
            var opField = new byte[17];
            var opBytes = Encoding.ASCII.GetBytes(OpFsCloseFile + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 17));
            writer.Write(opField);
            writer.Write(new byte[3]); // reserved (3 bytes)

            // Build request parameters
            writer.Write((uint)0); // principal
            writer.Write(fd);      // file handle

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x11);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return -1;

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            
            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }
            
            return errorCode;
        }
        catch
        {
            return -1;
        }
    }

    /// <summary>
    /// Create new file
    /// </summary>
    public static (int errorCode, int fd) MelFsCreateFile(M70Connection conn, string filename, int mode)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (18 bytes)
            var opField = new byte[18];
            var opBytes = Encoding.ASCII.GetBytes(OpFsCreateFile + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 18));
            writer.Write(opField);

            // Build request parameters  
            writer.Write((ushort)0); // reserved (2 bytes)
            writer.Write((uint)0);   // principal (4 bytes)
            writer.Write((uint)mode); // mode (4 bytes)
            writer.Write(filename.Length); // filename length (4 bytes)
            writer.Write(Encoding.ASCII.GetBytes(filename));

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x12);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return (-1, 0);

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            if (errorCode != 0)
                return (errorCode, 0);

            int fd = 0;

            // Read return value (4 bytes)
            if (remainingLength >= 4)
            {
                var retData = conn.ReceiveData(4);
                if (retData == null || retData.Length != 4)
                    return (-1, 0);
                remainingLength -= 4;
            }

            // Read file descriptor (4 bytes)
            if (remainingLength >= 4)
            {
                var fdData = conn.ReceiveData(4);
                if (fdData == null || fdData.Length != 4)
                    return (-1, 0);
                fd = BitConverter.ToInt32(fdData, 0);
                remainingLength -= 4;
            }

            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }

            return (0, fd);
        }
        catch
        {
            return (-1, 0);
        }
    }

    /// <summary>
    /// Write file data
    /// </summary>
    public static (int errorCode, int actualWritten) MelFsWriteFile(M70Connection conn, int fd, byte[] data, int writeSize)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (20 bytes)
            var opField = new byte[20];
            var opBytes = Encoding.ASCII.GetBytes(OpFsWriteFile + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 20));
            writer.Write(opField);

            // Build request parameters
            writer.Write((uint)0); // principal
            writer.Write(fd);      // file handle
            writer.Write(writeSize); // write size
            writer.Write(data, 0, writeSize);

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x11);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return (-1, 0);

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            if (errorCode != 0)
                return (errorCode, 0);

            int actualWritten = 0;

            // Read return value (4 bytes)
            if (remainingLength >= 4)
            {
                var retData = conn.ReceiveData(4);
                if (retData == null || retData.Length != 4)
                    return (-1, 0);
                remainingLength -= 4;
            }

            // Read actual written size (4 bytes)
            if (remainingLength >= 4)
            {
                var sizeData = conn.ReceiveData(4);
                if (sizeData == null || sizeData.Length != 4)
                    return (-1, 0);
                actualWritten = BitConverter.ToInt32(sizeData, 0);
                remainingLength -= 4;
            }

            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }

            return (0, actualWritten);
        }
        catch
        {
            return (-1, 0);
        }
    }

    /// <summary>
    /// Remove/delete file
    /// </summary>
    public static int MelFsRemoveFile(M70Connection conn, string filename)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (18 bytes)
            var opField = new byte[18];
            var opBytes = Encoding.ASCII.GetBytes(OpFsRemoveFile + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 18));
            writer.Write(opField);

            // Build request parameters
            writer.Write((ushort)0); // reserved (2 bytes)
            writer.Write((uint)0);   // principal (4 bytes)
            writer.Write(filename.Length); // filename length (4 bytes)
            writer.Write(Encoding.ASCII.GetBytes(filename));

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x12);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return -1;

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            
            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }
            
            return errorCode;
        }
        catch
        {
            return -1;
        }
    }

    /// <summary>
    /// Get file stat information
    /// </summary>
    public static (int errorCode, FileStatInfo? statInfo) MelFsStatFile(M70Connection conn, string filename)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (16 bytes)
            var opField = new byte[16];
            var opBytes = Encoding.ASCII.GetBytes(OpFsStatFile + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 16));
            writer.Write(opField);

            // Build request parameters
            writer.Write((uint)0);   // principal
            writer.Write(filename.Length); // filename length
            writer.Write(Encoding.ASCII.GetBytes(filename));

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x10);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return (-1, null);

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            if (errorCode != 0)
                return (errorCode, null);

            FileStatInfo? statInfo = null;

            // Read return value (4 bytes)
            if (remainingLength >= 4)
            {
                var retData = conn.ReceiveData(4);
                if (retData == null || retData.Length != 4)
                    return (-1, null);
                remainingLength -= 4;
            }

            // Read data_length (4 bytes)
            int dataLen = 0;
            if (remainingLength >= 4)
            {
                var dataLenData = conn.ReceiveData(4);
                if (dataLenData == null || dataLenData.Length != 4)
                    return (-1, null);
                dataLen = BitConverter.ToInt32(dataLenData, 0);
                remainingLength -= 4;

                // CRITICAL ALIGNMENT FIX:
                // Python version reads 16 bytes total for header (Ret+Len+Padding).
                // We have read 4 (Ret) + 4 (Len) = 8 bytes.
                // We must skip the next 8 bytes (Padding) to align with the struct start.
                if (remainingLength >= 8)
                {
                    conn.ReceiveData(8); // Consume padding
                    remainingLength -= 8;
                }

                // Read FileStat structure (64 bytes)
                if (dataLen >= 64 && remainingLength >= 64)
                {
                    var statData = conn.ReceiveData(64);
                    if (statData != null && statData.Length == 64)
                    {
                        // Parse: mode(4) + reserved1(8) + file_size(4) + reserved2(24) + time_fields(24)
                        int mode = BitConverter.ToInt32(statData, 0); // Offset 0
                        int fileSize = BitConverter.ToInt32(statData, 12); // Offset 12
                        
                        // Time fields at standard offsets (starting at 40)
                        int year = BitConverter.ToInt32(statData, 40);
                        int month = BitConverter.ToInt32(statData, 44);
                        int day = BitConverter.ToInt32(statData, 48);
                        int hour = BitConverter.ToInt32(statData, 52);
                        int minute = BitConverter.ToInt32(statData, 56);
                        int second = BitConverter.ToInt32(statData, 60);

                        // Console.WriteLine($"statData Raw: {BitConverter.ToString(statData)}");
                        // Console.WriteLine($"Stat - Mode: {mode}, Size: {fileSize}, Time: {year}-{month}-{day} {hour}:{minute}:{second}");

                        statInfo = new FileStatInfo
                        {
                            Mode = (uint)mode,
                            FileSize = (ulong)fileSize,
                            Year = (ushort)(1950 + year),
                            Month = (ushort)month,
                            Day = (ushort)day,
                            Hour = (ushort)hour,
                            Minute = (ushort)minute,
                            Second = (ushort)second
                        };
                        remainingLength -= 64;
                    }
                }
            }

            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }

            return (0, statInfo);
        }
        catch
        {
            return (-1, null);
        }
    }

    /// <summary>
    /// Open directory
    /// </summary>
    public static (int errorCode, int fd) MelFsOpenDirectory(M70Connection conn, string dirPath)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (24 bytes) - CRITICAL: This was missing!
            var opField = new byte[24];
            var opBytes = Encoding.ASCII.GetBytes(OpFsOpenDir + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 24));
            writer.Write(opField);

            // Build request parameters
            writer.Write((uint)0);   // principal
            writer.Write((uint)dirPath.Length); // path length
            writer.Write(Encoding.ASCII.GetBytes(dirPath));

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x15);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return (-1, 0);

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            if (errorCode != 0)
                return (errorCode, 0);

            int fd = 0;

            // Read return value (4 bytes)
            if (remainingLength >= 4)
            {
                var retData = conn.ReceiveData(4);
                if (retData == null || retData.Length != 4)
                    return (-1, 0);
                remainingLength -= 4;
            }

            // Read directory descriptor
            if (remainingLength >= 4)
            {
                var fdData = conn.ReceiveData(4);
                if (fdData == null || fdData.Length != 4)
                    return (-1, 0);
                fd = BitConverter.ToInt32(fdData, 0);
                remainingLength -= 4;
            }

            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }

            return (0, fd);
        }
        catch
        {
            return (-1, 0);
        }
    }

    /// <summary>
    /// Read directory entry
    /// </summary>
    public static (int errorCode, string? entryName) MelFsReadDirectory(M70Connection conn, int fd)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (24 bytes)
            var opField = new byte[24];
            var opBytes = Encoding.ASCII.GetBytes(OpFsReadDir + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 24));
            writer.Write(opField);

            // Build request parameters
            writer.Write((uint)0); // principal
            writer.Write((uint)fd); // directory handle

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x15);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return (-1, null);

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            if (errorCode != 0)
                return (errorCode, null);

            // Response format: ret(4) -> datasize(4) -> [ret2(4) -> size(4) -> dirname(size)]
            string? dirname = null;

            // Read ret (4 bytes)
            if (remainingLength >= 4)
            {
                var retData = conn.ReceiveData(4);
                if (retData == null || retData.Length != 4)
                    return (-1, null);
                remainingLength -= 4;
            }
            else
            {
                return (-1, null);
            }

            // Read datasize (4 bytes)
            if (remainingLength >= 4)
            {
                var datasizeData = conn.ReceiveData(4);
                if (datasizeData == null || datasizeData.Length != 4)
                    return (-1, null);

                int datasize = BitConverter.ToInt32(datasizeData, 0);
                remainingLength -= 4;

                if (datasize > 0)
                {
                    // Read ret2 (4 bytes)
                    if (remainingLength >= 4)
                    {
                        var ret2Data = conn.ReceiveData(4);
                        if (ret2Data == null || ret2Data.Length != 4)
                            return (-1, null);
                        remainingLength -= 4;
                    }

                    // Read size (4 bytes)
                    if (remainingLength >= 4)
                    {
                        var sizeData = conn.ReceiveData(4);
                        if (sizeData == null || sizeData.Length != 4)
                            return (-1, null);

                        int size = BitConverter.ToInt32(sizeData, 0);
                        remainingLength -= 4;

                        // Read directory name
                        if (size > 0 && remainingLength >= size)
                        {
                            var nameData = conn.ReceiveData(size);
                            if (nameData != null)
                            {
                                dirname = Encoding.ASCII.GetString(nameData).TrimEnd('\0', '\n');
                                remainingLength -= size;
                            }
                        }
                    }
                }
            }

            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }

            return (0, dirname);
        }
        catch
        {
            return (-1, null);
        }
    }

    /// <summary>
    /// Close directory
    /// </summary>
    public static int MelFsCloseDirectory(M70Connection conn, int fd)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field (24 bytes)
            var opField = new byte[24];
            var opBytes = Encoding.ASCII.GetBytes(OpFsCloseDir + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 24));
            writer.Write(opField);

            // Build request parameters
            writer.Write((uint)0); // principal
            writer.Write(fd);      // directory handle

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, 0x16);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return -1;

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            
            // Discard remaining data
            if (remainingLength > 0)
            {
                conn.ReceiveData(remainingLength);
            }
            
            return errorCode;
        }
        catch
        {
            return -1;
        }
    }

    /// <summary>
    /// Get data from CNC
    /// </summary>
    public static (int errorCode, object? data) MelGetData(
        M70Connection conn,
        int section,
        int subSection,
        int systemNo,
        int axisFlag,
        M70DataType dataType)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Write operation name (aligned to 16 bytes like C version)
            var opBytes = new byte[16];
            var opStr = Encoding.ASCII.GetBytes(OpGetData + "\0");
            Array.Copy(opStr, opBytes, Math.Min(opStr.Length, 16));
            writer.Write(opBytes);

            // Write parameters
            writer.Write((uint)0);        // principal
            writer.Write((uint)section);
            writer.Write((uint)subSection);
            writer.Write((uint)systemNo);
            writer.Write((uint)axisFlag);
            writer.Write((uint)0);        // u2
            writer.Write((uint)dataType);

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, OpGetData.Length + 1);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return (-1, null);

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            if (errorCode != 0)
                return (errorCode, null);

            // Parse response data
            if (remainingLength > 0)
            {
                var data = ParseGetDataResponse(conn, dataType, remainingLength);
                return (0, data);
            }

            return (0, null);
        }
        catch
        {
            return (-1, null);
        }
    }

    private static object? ParseGetDataResponse(M70Connection conn, M70DataType dataType, int length)
    {
        try
        {
            // Receive response header (12 bytes)
            var header = conn.ReceiveData(12);
            if (header == null || header.Length < 12)
                return null;

            uint u1 = BitConverter.ToUInt32(header, 0);
            uint respDataType = BitConverter.ToUInt32(header, 4);
            uint dataLength = BitConverter.ToUInt32(header, 8);

            // Receive actual data
            if (dataLength > 0)
            {
                var dataBytes = conn.ReceiveData((int)dataLength);
                if (dataBytes == null)
                    return null;

                return dataType switch
                {
                    M70DataType.Char => (sbyte)dataBytes[0],
                    M70DataType.UChar => dataBytes[0],
                    M70DataType.Short => BitConverter.ToInt16(dataBytes, 0),
                    M70DataType.UShort => BitConverter.ToUInt16(dataBytes, 0),
                    M70DataType.Long => BitConverter.ToInt32(dataBytes, 0),
                    M70DataType.UInt32 => BitConverter.ToUInt32(dataBytes, 0),
                    M70DataType.DLong => BitConverter.ToInt64(dataBytes, 0),
                    M70DataType.Double => BitConverter.ToDouble(dataBytes, 0),
                    M70DataType.Str => dataBytes,  // Return raw bytes for string
                    M70DataType.FloatBin => dataBytes,
                    M70DataType.ClctData => dataBytes,
                    _ => dataBytes
                };
            }

            // Discard remaining data
            int remaining = length - 12 - (int)dataLength;
            if (remaining > 0)
            {
                conn.ReceiveData(remaining);
            }

            return null;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>
    /// Get drive information from CNC
    /// Returns drive list in format: "DriveName:\r\nDriveName:\r\n...\0"
    /// </summary>
    public static (int errorCode, string? driveInfo) MelFsGetDriveInformation(M70Connection conn)
    {
        try
        {
            using var ms = new MemoryStream();
            using var writer = new BinaryWriter(ms);

            // Build op field - "mochaFSGetDriveInformation" is 27 chars, padded to 28 bytes
            var opField = new byte[28];
            var opBytes = Encoding.ASCII.GetBytes(OpFsGetDriveInfo + "\0");
            Array.Copy(opBytes, opField, Math.Min(opBytes.Length, 28));
            writer.Write(opField);

            // Build request parameters (just principal, no other params needed)
            writer.Write((uint)0);   // principal

            var paramData = ms.ToArray();
            var requestHeader = BuildRequestHeader(conn, OpFsGetDriveInfo.Length + 1);
            var giopHeader = BuildGiopHeader(conn, requestHeader.Length + paramData.Length);

            // Send request
            var fullRequest = giopHeader.Concat(requestHeader).Concat(paramData).ToArray();
            if (conn.SendData(fullRequest) <= 0)
                return (-1, null);

            // Receive response
            var (errorCode, remainingLength) = ReceiveResponse(conn);
            Console.WriteLine($"[DEBUG] GetDriveInfo response: error={errorCode}, remaining={remainingLength}");
            if (errorCode != 0)
                return (errorCode, null);

            // Read response data
            if (remainingLength > 0)
            {
                // Read return value (4 bytes)
                if (remainingLength >= 4)
                {
                    var retData = conn.ReceiveData(4);
                    if (retData == null || retData.Length != 4)
                        return (-1, null);
                    int ret = BitConverter.ToInt32(retData, 0);
                    remainingLength -= 4;

                    // If ret > 0, it's the size of drive info data
                    if (ret > 0 && remainingLength >= 4)
                    {
                        // Read data length (4 bytes)
                        var dataLenBytes = conn.ReceiveData(4);
                        if (dataLenBytes == null || dataLenBytes.Length != 4)
                            return (-1, null);
                        int dataLen = BitConverter.ToInt32(dataLenBytes, 0);
                        remainingLength -= 4;

                        // Read actual drive info string
                        if (dataLen > 0 && remainingLength >= dataLen)
                        {
                            var driveData = conn.ReceiveData(dataLen);
                            if (driveData != null)
                            {
                                // Decode as UTF-8 or ASCII
                                string driveInfo = Encoding.UTF8.GetString(driveData).TrimEnd('\0');
                                remainingLength -= dataLen;

                                // Discard remaining data
                                if (remainingLength > 0)
                                {
                                    conn.ReceiveData(remainingLength);
                                }

                                return (0, driveInfo);
                            }
                        }
                    }
                }

                // Discard remaining data
                if (remainingLength > 0)
                {
                    conn.ReceiveData(remainingLength);
                }
            }

            return (errorCode, null);
        }
        catch
        {
            return (-1, null);
        }
    }

}


