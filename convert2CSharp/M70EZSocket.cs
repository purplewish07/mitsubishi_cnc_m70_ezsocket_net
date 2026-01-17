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
    /// List directory contents
    /// </summary>
    public static (M70ErrorCode errorCode, List<string>? files) ListDirectory(
        M70Connection conn, 
        string dirPath)
    {
        try
        {
            var (openError, fd) = M70GIOP.MelFsOpenDirectory(conn, dirPath);
            if (openError != 0 || fd == 0)
                return (M70ErrorCode.Failed, null);

            try
            {
                var files = new List<string>();

                while (true)
                {
                    var (readError, entryName) = M70GIOP.MelFsReadDirectory(conn, fd);
                    
                    if (readError != 0 || string.IsNullOrEmpty(entryName))
                        break;

                    files.Add(entryName);
                }

                return (M70ErrorCode.OK, files);
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
}
