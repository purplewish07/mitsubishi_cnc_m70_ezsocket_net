namespace MitsubishiCncM70;

/// <summary>
/// High-level M70 EZSocket API
/// Provides convenient methods for CNC operations
/// </summary>
public static class M70EZSocket
{
    /// <summary>
    /// Read file from CNC (high-level wrapper)
    /// </summary>
    public static (M70ErrorCode errorCode, byte[]? data) ReadFile(
        M70Connection conn, 
        string filepath, 
        int maxSize = 1000)
    {
        try
        {
            // Open file for reading
            var (openError, fd) = M70GIOP.MelFsOpenFile(conn, filepath, 0);
            if (openError != 0 || fd == 0)
                return (M70ErrorCode.Failed, null);

            try
            {
                var fileData = new List<byte>();
                int totalRead = 0;

                while (totalRead < maxSize)
                {
                    int chunkSize = Math.Min(1000, maxSize - totalRead);
                    var (readError, actualSize, chunk) = M70GIOP.MelFsReadFile(conn, fd, chunkSize);
                    
                    if (readError != 0 || chunk == null || actualSize == 0)
                        break;

                    fileData.AddRange(chunk.Take(actualSize));
                    totalRead += actualSize;

                    if (actualSize < chunkSize)
                        break;
                }

                return (M70ErrorCode.OK, fileData.ToArray());
            }
            finally
            {
                M70GIOP.MelFsCloseFile(conn, fd);
            }
        }
        catch
        {
            return (M70ErrorCode.Failed, null);
        }
    }

    /// <summary>
    /// Write file to CNC (high-level wrapper)
    /// </summary>
    public static M70ErrorCode WriteFile(
        M70Connection conn, 
        string filepath, 
        byte[] data,
        bool overwrite = true)
    {
        try
        {
            // Check if file exists
            var (statError, statInfo) = M70GIOP.MelFsStatFile(conn, filepath);
            
            // If stat succeeded (error == 0) and file exists
            if (statError == 0 && statInfo != null)
            {
                if (!overwrite)
                    return M70ErrorCode.Failed;
                
                // Delete existing file
                var deleteError = M70GIOP.MelFsRemoveFile(conn, filepath);
                if (deleteError != 0)
                    return M70ErrorCode.Failed;
            }
            // If statError != 0, file might not exist, which is OK for creating new file

            // Create new file
            var (createError, fd) = M70GIOP.MelFsCreateFile(conn, filepath, 1);
            if (createError != 0 || fd == 0)
                return M70ErrorCode.Failed;

            try
            {
                int totalWritten = 0;
                int chunkSize = 1000;

                while (totalWritten < data.Length)
                {
                    int writeSize = Math.Min(chunkSize, data.Length - totalWritten);
                    var chunk = new byte[writeSize];
                    Array.Copy(data, totalWritten, chunk, 0, writeSize);

                    var (writeError, actualWritten) = M70GIOP.MelFsWriteFile(conn, fd, chunk, writeSize);
                    if (writeError != 0)
                        return M70ErrorCode.Failed;

                    totalWritten += actualWritten;

                    if (actualWritten < writeSize)
                        break;
                }

                return totalWritten == data.Length ? M70ErrorCode.OK : M70ErrorCode.Failed;
            }
            finally
            {
                M70GIOP.MelFsCloseFile(conn, fd);
            }
        }
        catch
        {
            return M70ErrorCode.Failed;
        }
    }

    /// <summary>
    /// Delete file from CNC
    /// </summary>
    public static M70ErrorCode DeleteFile(M70Connection conn, string filepath)
    {
        try
        {
            var errorCode = M70GIOP.MelFsRemoveFile(conn, filepath);
            return errorCode == 0 ? M70ErrorCode.OK : M70ErrorCode.Failed;
        }
        catch
        {
            return M70ErrorCode.Failed;
        }
    }

    /// <summary>
    /// Get file information
    /// </summary>
    public static (M70ErrorCode errorCode, FileStatInfo? info) StatFile(
        M70Connection conn, 
        string filepath)
    {
        try
        {
            var (errorCode, statInfo) = M70GIOP.MelFsStatFile(conn, filepath);
            return errorCode == 0 
                ? (M70ErrorCode.OK, statInfo) 
                : (M70ErrorCode.Failed, null);
        }
        catch
        {
            return (M70ErrorCode.Failed, null);
        }
    }

    /// <summary>
    /// Download file from CNC and save to local path
    /// </summary>
    public static M70ErrorCode DownloadFile(
        M70Connection conn,
        string remotePath,
        string localPath,
        int maxSize = 1000000)
    {
        try
        {
            var (errorCode, data) = ReadFile(conn, remotePath, maxSize);
            if (errorCode != M70ErrorCode.OK || data == null)
                return errorCode;

            File.WriteAllBytes(localPath, data);
            return M70ErrorCode.OK;
        }
        catch
        {
            return M70ErrorCode.Failed;
        }
    }

    /// <summary>
    /// Upload file from local path to CNC
    /// </summary>
    public static M70ErrorCode UploadFile(
        M70Connection conn,
        string localPath,
        string remotePath,
        bool overwrite = true)
    {
        try
        {
            if (!File.Exists(localPath))
                return M70ErrorCode.Failed;

            var data = File.ReadAllBytes(localPath);
            return WriteFile(conn, remotePath, data, overwrite);
        }
        catch
        {
            return M70ErrorCode.Failed;
        }
    }

    // ============================================================
    // CNC Information Methods
    // ============================================================

    /// <summary>
    /// Read NC name version
    /// </summary>
    public static (M70ErrorCode errorCode, string version) ReadNcNameVersion(M70Connection conn)
    {
        return ReadVersion(conn, 68, 1);
    }

    /// <summary>
    /// Read PLC version
    /// </summary>
    public static (M70ErrorCode errorCode, string version) ReadPlcVersion(M70Connection conn)
    {
        return ReadVersion(conn, 67, 2);
    }

    /// <summary>
    /// Read CNC machine type (MC or Lathe)
    /// </summary>
    public static (M70ErrorCode errorCode, M70NCMachineType machineType) ReadMachineType(M70Connection conn)
    {
        if (!conn.IsConnected)
            return (M70ErrorCode.Failed, M70NCMachineType.MC);

        var (ret, data) = M70GIOP.MelGetData(conn, 2, 100, 0, 0, M70DataType.Char);
        
        if (ret == 0 && data != null)
        {
            try
            {
                byte typeValue = data switch
                {
                    sbyte sb => (byte)sb,
                    byte b => b,
                    _ => 0
                };

                var machineType = typeValue == 1 ? M70NCMachineType.Lathe : M70NCMachineType.MC;
                return (M70ErrorCode.OK, machineType);
            }
            catch
            {
                return (M70ErrorCode.Failed, M70NCMachineType.MC);
            }
        }

        return (M70ErrorCode.Failed, M70NCMachineType.MC);
    }

    private static (M70ErrorCode errorCode, string version) ReadVersion(
        M70Connection conn, 
        int section, 
        int subSection)
    {
        if (!conn.IsConnected)
            return (M70ErrorCode.Failed, string.Empty);

        var (ret, data) = M70GIOP.MelGetData(conn, section, subSection, 0, 0, M70DataType.Str);
        
        if (ret == 0 && data is byte[] bytes)
        {
            try
            {
                // Decode UTF-8 and remove null terminators
                string version = System.Text.Encoding.UTF8.GetString(bytes).TrimEnd('\0');
                return (M70ErrorCode.OK, version);
            }
            catch
            {
                // If decode fails, return hex string
                return (M70ErrorCode.OK, BitConverter.ToString(bytes).Replace("-", ""));
            }
        }

        return (M70ErrorCode.Failed, string.Empty);
    }

    /// <summary>
    /// Get drive information from CNC
    /// Returns list of available drives
    /// </summary>
    public static (M70ErrorCode errorCode, List<string>? drives) GetDriveInformation(M70Connection conn)
    {
        if (!conn.IsConnected)
            return (M70ErrorCode.Failed, null);

        var (ret, driveInfo) = M70GIOP.MelFsGetDriveInformation(conn);
        
        if (ret == 0 && !string.IsNullOrEmpty(driveInfo))
        {
            try
            {
                // Parse drive info format: "DriveName:\r\nDriveName:\r\n...\0"
                var drives = new List<string>();
                var lines = driveInfo.Split(new[] { "\r\n", "\n" }, StringSplitOptions.RemoveEmptyEntries);
                
                foreach (var line in lines)
                {
                    var trimmed = line.Trim();
                    if (!string.IsNullOrEmpty(trimmed))
                    {
                        // Remove trailing colon if present
                        if (trimmed.EndsWith(":"))
                            trimmed = trimmed.Substring(0, trimmed.Length - 1);
                        drives.Add(trimmed);
                    }
                }

                return (M70ErrorCode.OK, drives);
            }
            catch
            {
                return (M70ErrorCode.Failed, null);
            }
        }

        return (M70ErrorCode.Failed, null);
    }

    /// <summary>
    /// List directory contents with optional detailed information
    /// </summary>
    public static (M70ErrorCode errorCode, List<Dictionary<string, object>>? entries) ListDirectory(
        M70Connection conn,
        string dirPath,
        bool includeDetails = true)
    {
        try
        {
            var (openError, fd) = M70GIOP.MelFsOpenDirectory(conn, dirPath);
            if (openError != 0 || fd == 0)
                return (M70ErrorCode.Failed, null);

            try
            {
                var entries = new List<Dictionary<string, object>>();

                while (true)
                {
                    var (readError, filename) = M70GIOP.MelFsReadDirectory(conn, fd);

                    if (readError != 0 || string.IsNullOrEmpty(filename))
                        break;

                    if (!includeDetails)
                    {
                        entries.Add(new Dictionary<string, object> { { "name", filename } });
                        continue;
                    }

                    // Get detailed file information
                    var fullPath = System.IO.Path.Combine(dirPath, filename);
                    var (statError, fileStat) = M70GIOP.MelFsStatFile(conn, fullPath);

                    if (statError != 0 || fileStat == null)
                        continue;

                    var entry = new Dictionary<string, object>
                    {
                        { "name", filename },
                        { "type", fileStat.Mode == 0x4000 ? "D" : "F" },
                        { "size", fileStat.FileSize },
                        { "date", fileStat.GetModifiedDate() },
                        { "comment", "" }
                    };

                    if (fileStat.Mode != 0x4000 && fileStat.FileSize > 0) // If it's a file
                    {
                        var (readErr, data) = ReadFile(conn, fullPath, 50);
                        if (readErr == M70ErrorCode.OK && data != null)
                        {
                            var text = System.Text.Encoding.ASCII.GetString(data).TrimEnd('\0');
                            if (text.Contains("(") && text.Contains(")"))
                            {
                                var start = text.IndexOf('(');
                                var end = text.IndexOf(')', start) + 1;
                                entry["comment"] = text.Substring(start, end - start);
                            }
                            else
                            {
                                entry["comment"] = text.Split('\n')[0].Trim('\r');
                            }
                        }
                    }
                    else if (fileStat.Mode == 0x4000) // If it's a directory
                    {
                        entry["datetime"] = DBNull.Value; // 或 DateTime.MinValue
                        entry["comment"] = string.Empty; // 或其他適當的預設值
                    }

                    entries.Add(entry);
                }

                return (M70ErrorCode.OK, entries);
            }
            finally
            {
                M70GIOP.MelFsCloseDirectory(conn, fd);
            }
        }
        catch
        {
            return (M70ErrorCode.Failed, null);
        }
    }

    // ============================================================
    // Program Management Methods
    // ============================================================

    /// <summary>
    /// Read main program name
    /// </summary>
    /// <param name="conn">CNC connection</param>
    /// <param name="systemNo">System number (default 1)</param>
    /// <param name="nameType">Program name type (default ProgramNo)</param>
    /// <returns>Tuple of (error_code, program_name)</returns>
    public static (M70ErrorCode errorCode, string programName) ReadMainProgramName(
        M70Connection conn, 
        int systemNo = 1, 
        ProgramNameType nameType = ProgramNameType.ProgramNo)
    {
        return ReadProgramName(conn, 45, 101, systemNo, nameType);
    }

    /// <summary>
    /// Internal method to read program names
    /// </summary>
    /// <param name="conn">CNC connection</param>
    /// <param name="section">GIOP section</param>
    /// <param name="baseSub">Base sub-section number</param>
    /// <param name="systemNo">System number</param>
    /// <param name="nameType">Program name type</param>
    /// <returns>Tuple of (error_code, program_name)</returns>
    private static (M70ErrorCode errorCode, string programName) ReadProgramName(
        M70Connection conn,
        int section,
        int baseSub,
        int systemNo,
        ProgramNameType nameType)
    {
        if (!conn.IsConnected)
            return (M70ErrorCode.Failed, string.Empty);

        try
        {
            int subSection = baseSub + (int)nameType;

            // SequenceNumber and BlockNumber use DLong, others use Str
            if (nameType == ProgramNameType.SequenceNumber || nameType == ProgramNameType.BlockNumber)
            {
                var (ret, data) = M70GIOP.MelGetData(conn, section, subSection, systemNo, 0, M70DataType.DLong);
                if (ret == 0 && data != null)
                {
                    return (M70ErrorCode.OK, data.ToString() ?? string.Empty);
                }
                return (M70ErrorCode.Failed, string.Empty);
            }
            else
            {
                var (ret, data) = M70GIOP.MelGetData(conn, section, subSection, systemNo, 0, M70DataType.Str);
                if (ret == 0 && data is byte[] bytes)
                {
                    try
                    {
                        string programName = System.Text.Encoding.UTF8.GetString(bytes)
                            .TrimEnd('\0')
                            .Trim();
                        return (M70ErrorCode.OK, programName);
                    }
                    catch
                    {
                        return (M70ErrorCode.OK, string.Empty);
                    }
                }
                return (M70ErrorCode.Failed, string.Empty);
            }
        }
        catch
        {
            return (M70ErrorCode.Failed, string.Empty);
        }
    }
}
