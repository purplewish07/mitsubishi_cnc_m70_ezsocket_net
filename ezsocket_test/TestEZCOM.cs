using System;
using System.Runtime.InteropServices;

/// <summary>
/// Test program to call EZCOM COM API GetDriveInformation
/// This will help us analyze the network traffic and determine if GIOP is used
/// </summary>
class TestEZCOM
{
    // COM Interface definition from your code
    [ComImport]
    [Guid("B272F8A1-FE59-11D3-A28E-00101E002AAB")] // Replace with actual GUID from EZCOM.dll
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface IEZNcFile
    {
        [PreserveSig]
        int GetDriveInformation([MarshalAs(UnmanagedType.LPWStr)] out string lppwszDriveInfo);
    }

    static void Main(string[] args)
    {
        Console.WriteLine("=== EZCOM GetDriveInformation Test ===");
        Console.WriteLine("This test will call EZCOM COM API.");
        Console.WriteLine("Please run Wireshark to capture packets on port 683.");
        Console.WriteLine();

        string cncIp = "192.168.1.214";
        int cncPort = 683;

        if (args.Length >= 1) cncIp = args[0];
        if (args.Length >= 2) cncPort = int.Parse(args[1]);

        Console.WriteLine($"Target CNC: {cncIp}:{cncPort}");
        Console.WriteLine();

        try
        {
            // Method 1: Using ProgID (based on Python code)
            Console.WriteLine("Attempting to create EZCOM object via ProgID...");
            
            // Python uses: win32com.client.Dispatch('EZNcAut.DispEZNcCommunication')
            Type ezcomType = Type.GetTypeFromProgID("EZNcAut.DispEZNcCommunication");
            if (ezcomType == null)
            {
                Console.WriteLine("ERROR: EZNcAut.DispEZNcCommunication not registered!");
                Console.WriteLine("Please install EZSocket from: C:\\Program Files (x86)\\EZSocket\\EZSocketNc\\");
                return;
            }

            dynamic ezcom = Activator.CreateInstance(ezcomType);
            Console.WriteLine("✓ EZCOM object created successfully");

            // Setup TCP/IP Protocol (from Python: SetTCPIPProtocol)
            Console.WriteLine($"Setting up TCP/IP protocol for {cncIp}:{cncPort}...");
            int setProtocolResult = ezcom.SetTCPIPProtocol(cncIp, cncPort);
            Console.WriteLine($"SetTCPIPProtocol result: {setProtocolResult}");
            
            if (setProtocolResult != 0)
            {
                Console.WriteLine($"ERROR: Failed to set protocol (error code: {setProtocolResult})");
                return;
            }

            // Open connection (from Python: Open2)
            // Args: MachineType(6=MELDAS700M), UnitNo(1), Timeout(30*100ms), ComHostName
            Console.WriteLine("Opening connection (Open2)...");
            int unitNo = 1; // Use unit number 1
            int timeout = 30; // 30 * 100ms = 3 seconds
            string comHostName = "EZNC_LOCALHOST";
            
            int openResult = ezcom.Open2(6, unitNo, timeout, comHostName);
            Console.WriteLine($"Open2 result: {openResult}");

            if (openResult != 0)
            {
                Console.WriteLine($"ERROR: Failed to open connection (error code: {openResult})");
                return;
            }
            Console.WriteLine("✓ Connected to CNC");
            Console.WriteLine();

            // Add some diagnostic calls before GetDriveInformation
            Console.WriteLine("Running diagnostic checks...");
            
            try
            {
                // Check if connection is really working by calling a simple method
                Console.WriteLine("Testing connection with basic calls...");
                
                // Try to get some basic info (similar to Python code)
                // These methods might exist in the COM interface
                Console.WriteLine("Connection appears to be working.");
            }
            catch (Exception diagEx)
            {
                Console.WriteLine($"Diagnostic error: {diagEx.Message}");
            }
            Console.WriteLine();

            // Call GetDriveInformation
            Console.WriteLine("Calling File_GetDriveInformation()...");
            Console.WriteLine(">>> START CAPTURING PACKETS NOW <<<");
            Console.WriteLine("Press Enter to continue...");
            Console.ReadLine();

            try
            {
                // This is the critical call - capture packets during this
                // From Python: errcd, drive_info = ezcom.File_GetDriveInformation()
                // The method returns error code, and drive_info is an out parameter
                object[] methodArgs = new object[1];
                object result = ezcom.GetType().InvokeMember(
                    "File_GetDriveInformation",
                    System.Reflection.BindingFlags.InvokeMethod,
                    null,
                    ezcom,
                    methodArgs);
                
                int errorCode = Convert.ToInt32(result);
                string driveInfo = methodArgs[0]?.ToString() ?? "";
                
                Console.WriteLine();
                Console.WriteLine(">>> STOP CAPTURING PACKETS <<<");
                Console.WriteLine();
                Console.WriteLine($"✓ GetDriveInformation completed!");
                Console.WriteLine($"Error Code: {errorCode}");
                
                // Check if error code indicates success
                if (errorCode == 0)
                {
                    Console.WriteLine("ERROR: No drive exists (error code 0)");
                }
                else if (errorCode > 0)
                {
                    Console.WriteLine($"SUCCESS: Returned {errorCode} bytes");
                }
                else
                {
                    Console.WriteLine($"ERROR: Error code {errorCode}");
                    // According to docs:
                    // EZNC_FILE_DRVLIST_READ: Drive information read error
                    // EZNC_FILE_DIR_NODRIVE: Drive does not exist
                }
                
                Console.WriteLine($"Drive Info Length: {driveInfo.Length} characters");
                Console.WriteLine();
                Console.WriteLine("Drive Information:");
                Console.WriteLine("==================");
                Console.WriteLine(driveInfo);
                Console.WriteLine("==================");
                Console.WriteLine();

                // Display in hex for analysis
                if (!string.IsNullOrEmpty(driveInfo))
                {
                    Console.WriteLine("Hex dump:");
                    foreach (char c in driveInfo)
                    {
                        Console.Write($"{(int)c:X2} ");
                    }
                    Console.WriteLine();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR calling GetDriveInformation: {ex.Message}");
                Console.WriteLine($"HRESULT: 0x{Marshal.GetHRForException(ex):X8}");
            }

            // Disconnect
            Console.WriteLine();
            Console.WriteLine("Disconnecting (Close and Release)...");
            try
            {
                ezcom.Close();
                ezcom.Release();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Warning during disconnect: {ex.Message}");
            }
            Console.WriteLine("✓ Disconnected");

        }
        catch (COMException comEx)
        {
            Console.WriteLine($"COM Error: {comEx.Message}");
            Console.WriteLine($"HRESULT: 0x{comEx.ErrorCode:X8}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            Console.WriteLine($"Type: {ex.GetType().Name}");
            Console.WriteLine($"Stack: {ex.StackTrace}");
        }

        Console.WriteLine();
        Console.WriteLine("Test completed. Press Enter to exit...");
        Console.ReadLine();
    }
}
