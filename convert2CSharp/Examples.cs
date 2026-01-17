using MitsubishiCncM70;

// ============================================================
// Configuration - Modify these values for your CNC machine
// ============================================================
const string CNC_IP = "192.168.1.214";
const int CNC_PORT = 683;
const M70NCType NC_TYPE = M70NCType.Meldas700M;
// ============================================================

// Example 1: List directory
Console.WriteLine("=== Example 1: List Directory ===");
using (var conn = new M70Connection(CNC_IP, CNC_PORT, NC_TYPE))
{
    if (conn.Connect())
    {
        Console.WriteLine("Connected to CNC");

        var (errorCode, files) = M70EZSocket.ListDirectory(
            conn,
            @"M01:\PRG\USER\"
        );

        if (errorCode == M70ErrorCode.OK && files != null)
        {
            Console.WriteLine($"Found {files.Count} files:");
            int count = 0;
            string? firstNcFile = null;
            foreach (var file in files)
            {
                Console.WriteLine($"  {++count:D2}. {file}");
                // Find first .NC file
                if (firstNcFile == null && file.ToUpper().EndsWith(".NC"))
                {
                    firstNcFile = file;
                }
            }
            
            // Download first .NC file if found
            if (firstNcFile != null)
            {
                // firstNcFile = "O3000.NC"; // Hardcode for testing
                Console.WriteLine($"\n=== Example 2: Download First .NC File ({firstNcFile}) ===");
                var downloadResult = M70EZSocket.DownloadFile(
                    conn,
                    $@"M01:\PRG\USER\{firstNcFile}",
                    // firstNcFile
                    $"downloaded_{firstNcFile}"
                );

                if (downloadResult == M70ErrorCode.OK)
                    Console.WriteLine($"✓ File {firstNcFile} downloaded successfully");
                else
                    Console.WriteLine($"✗ Download failed");
            }
        }
        else
        {
            Console.WriteLine("✗ Failed to list directory");
        }

        conn.Disconnect();
    }
}

Console.WriteLine();

// Example 3: Upload file
Console.WriteLine("=== Example 3: Upload File (O3000.NC) ===");
using (var conn = new M70Connection(CNC_IP, CNC_PORT, NC_TYPE))
{
    if (conn.Connect())
    {
        Console.WriteLine("Connected to CNC");

        // Create a test file to upload
        string testFile = "O3000.NC";
        string testContent = @"%
O3000(TEST PROGRAM O3000)
(UPLOAD AND DELETE TEST)
N1
M30
%";
        System.IO.File.WriteAllText(testFile, testContent);

        var result = M70EZSocket.UploadFile(
            conn,
            testFile,
            @"M01:\PRG\USER\O3000.NC",
            overwrite: true
        );

        if (result == M70ErrorCode.OK)
            Console.WriteLine("✓ File uploaded successfully");
        else
            Console.WriteLine($"✗ Upload failed: {result}");

        conn.Disconnect();
    }
}

Console.WriteLine();

//Example 4: Delete file
Console.WriteLine("=== Example 4: Delete File (O3000.NC) ===");
using (var conn = new M70Connection(CNC_IP, CNC_PORT, NC_TYPE))
{
    if (conn.Connect())
    {
        Console.WriteLine("Connected to CNC");

        var result = M70EZSocket.DeleteFile(
            conn,
            @"M01:\PRG\USER\O3000.NC"  // Delete the test file we just uploaded
        );

        if (result == M70ErrorCode.OK)
            Console.WriteLine("✓ File deleted successfully");
        else
            Console.WriteLine("✗ Delete failed");

        conn.Disconnect();
    }
}

Console.WriteLine();

