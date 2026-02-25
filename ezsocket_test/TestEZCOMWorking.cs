using System;

/// <summary>
/// Working EZCOM test - Direct dynamic call (not reflection)
/// Successfully retrieves drive information from M70 CNC
/// </summary>
class TestEZCOMWorking
{
    static void Main(string[] args)
    {
        Console.WriteLine("=== EZCOM File_GetDriveInformation Test ===");
        Console.WriteLine();

        string host = "192.168.1.214:683";
        if (args.Length >= 1) host = args[0];

        string[] parts = host.Split(':');
        string ip = parts[0];
        int port = int.Parse(parts[1]);

        Console.WriteLine($"Target: {ip}:{port}");
        Console.WriteLine();

        try
        {
            // Create COM object
            Console.WriteLine("Creating COM object...");
            Type ezcomType = Type.GetTypeFromProgID("EZNcAut.DispEZNcCommunication");
            if (ezcomType == null)
            {
                Console.WriteLine("ERROR: COM object 'EZNcAut.DispEZNcCommunication' not registered!");
                return;
            }
            dynamic ezcom = Activator.CreateInstance(ezcomType);
            Console.WriteLine("✓ Created");
            Console.WriteLine();

            // Connect
            Console.WriteLine("Connecting...");
            int errcd = ezcom.SetTCPIPProtocol(ip, port);
            if (errcd != 0)
            {
                Console.WriteLine($"ERROR: SetTCPIPProtocol failed with code {errcd}");
                return;
            }

            errcd = ezcom.Open2(6, 1, 30, "EZNC_LOCALHOST");
            if (errcd != 0)
            {
                Console.WriteLine($"ERROR: Open2 failed with code {errcd}");
                return;
            }
            Console.WriteLine("✓ Connected");
            Console.WriteLine();

            // Call File_GetDriveInformation
            Console.WriteLine("=== Wireshark Capture Instructions ===");
            Console.WriteLine("1. Start Wireshark");
            Console.WriteLine("2. Filter: tcp.port == 683");
            Console.WriteLine("3. Start capture");
            Console.WriteLine("4. Press Enter below");
            Console.WriteLine();
            Console.WriteLine("Press Enter to call File_GetDriveInformation()...");
            Console.ReadLine();

            Console.WriteLine("Calling File_GetDriveInformation()...");
            
            // The correct way: direct dynamic call with out parameter
            string driveInfo = "";
            errcd = ezcom.File_GetDriveInformation(out driveInfo);
            
            Console.WriteLine();
            Console.WriteLine("=== Result ===");
            Console.WriteLine($"Return Code: {errcd}");
            Console.WriteLine($"Drive Info: '{driveInfo}'");
            Console.WriteLine($"Length: {driveInfo.Length} bytes");
            Console.WriteLine();

            if (driveInfo.Length > 0)
            {
                Console.WriteLine("Hex Dump:");
                for (int i = 0; i < driveInfo.Length; i++)
                {
                    Console.Write($" {(int)driveInfo[i]:X2}");
                    if ((i + 1) % 16 == 0 || i == driveInfo.Length - 1)
                    {
                        Console.Write("  ");
                        int start = (i / 16) * 16;
                        for (int j = start; j <= i; j++)
                        {
                            char c = driveInfo[j];
                            if (c == '\r') Console.Write("\\r");
                            else if (c == '\n') Console.Write("\\n");
                            else if (c >= 32 && c < 127) Console.Write(c);
                            else Console.Write('.');
                        }
                        Console.WriteLine();
                    }
                }
                Console.WriteLine();

                // Parse drive names
                Console.WriteLine("Available Drives:");
                string[] drives = driveInfo.Split(new[] { "\r\n" }, StringSplitOptions.RemoveEmptyEntries);
                foreach (string drive in drives)
                {
                    if (!string.IsNullOrWhiteSpace(drive))
                    {
                        Console.WriteLine($"  - {drive}");
                    }
                }
            }

            // Test other methods
            // (Commented out for clean Wireshark packet capture analysis)
            /*
            Console.WriteLine();
            Console.WriteLine("=== Testing Other Methods ===");
            
            Console.WriteLine("System_GetVersion(1, 0)...");
            string version = "";
            errcd = ezcom.System_GetVersion(1, 0, out version);
            Console.WriteLine($"  Result: {errcd}, Version: '{version}'");
            */
            
            // Close
            Console.WriteLine();
            Console.WriteLine("Closing connection...");
            ezcom.Close();
            Console.WriteLine("✓ Closed");
        }
        catch (Microsoft.CSharp.RuntimeBinder.RuntimeBinderException ex)
        {
            Console.WriteLine($"Runtime Binding Error: {ex.Message}");
            Console.WriteLine();
            Console.WriteLine("This usually means the method signature doesn't match.");
            Console.WriteLine("The COM method may not support 'out' parameters in C#.");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: {ex.Message}");
            Console.WriteLine($"Type: {ex.GetType().Name}");
            if (ex.InnerException != null)
            {
                Console.WriteLine($"Inner: {ex.InnerException.Message}");
            }
        }

        Console.WriteLine();
        Console.WriteLine("Press Enter to exit...");
        Console.ReadLine();
    }
}
