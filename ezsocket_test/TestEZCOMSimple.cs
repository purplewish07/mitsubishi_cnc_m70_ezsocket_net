using System;
using System.Runtime.InteropServices;

/// <summary>
/// Simplified test that exactly mirrors the Python code
/// This should work identically to the Python version
/// </summary>
class TestEZCOMSimple
{
    static void Main(string[] args)
    {
        Console.WriteLine("=== Simple EZCOM Test (Mirroring Python) ===");
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
            // Step 1: Create COM object (same as Python)
            Console.WriteLine("1. Creating EZNcAut.DispEZNcCommunication...");
            Type ezcomType = Type.GetTypeFromProgID("EZNcAut.DispEZNcCommunication");
            if (ezcomType == null)
            {
                Console.WriteLine("ERROR: COM object not registered!");
                return;
            }
            dynamic ezcom = Activator.CreateInstance(ezcomType);
            Console.WriteLine("   ✓ Created");

            // Step 2: SetTCPIPProtocol (same as Python)
            Console.WriteLine($"2. Calling SetTCPIPProtocol('{ip}', {port})...");
            int errcd = ezcom.SetTCPIPProtocol(ip, port);
            Console.WriteLine($"   Result: {errcd}");
            if (errcd != 0)
            {
                Console.WriteLine($"   ERROR: SetTCPIPProtocol failed!");
                return;
            }

            // Step 3: Allocate unit number (Python uses 1)
            int unitno = 1;
            Console.WriteLine($"3. Using unit number: {unitno}");

            // Step 4: Open2 (same as Python)
            // Args: MachineType(6), UnitNo, Timeout(30), ComHostName
            Console.WriteLine("4. Calling Open2(6, 1, 30, 'EZNC_LOCALHOST')...");
            errcd = ezcom.Open2(6, unitno, 30, "EZNC_LOCALHOST");
            Console.WriteLine($"   Result: {errcd}");
            if (errcd != 0)
            {
                Console.WriteLine($"   ERROR: Open2 failed!");
                return;
            }
            Console.WriteLine("   ✓ Connected");
            Console.WriteLine();

            // Step 5: File_GetDriveInformation (same as Python)
            Console.WriteLine("5. Calling File_GetDriveInformation()...");
            Console.WriteLine("   >>> START WIRESHARK CAPTURE NOW <<<");
            Console.WriteLine("   Press Enter to call the method...");
            Console.ReadLine();

            // Python: errcd, drive_info = self.__ezcom.File_GetDriveInformation()
            // Try direct dynamic call instead of reflection
            string drive_info = "";
            try
            {
                // Attempt 1: Direct call with out parameter
                errcd = ezcom.File_GetDriveInformation(out drive_info);
            }
            catch (Microsoft.CSharp.RuntimeBinder.RuntimeBinderException ex1)
            {
                Console.WriteLine($"   Attempt 1 failed: {ex1.Message}");
                
                try
                {
                    // Attempt 2: Call without parameters and get tuple
                    var result = ezcom.File_GetDriveInformation();
                    
                    // Check if result is an array/tuple
                    if (result is object[] resultArray && resultArray.Length >= 2)
                    {
                        errcd = Convert.ToInt32(resultArray[0]);
                        drive_info = resultArray[1]?.ToString() ?? "";
                    }
                    else
                    {
                        errcd = Convert.ToInt32(result);
                    }
                }
                catch (Exception ex2)
                {
                    Console.WriteLine($"   Attempt 2 failed: {ex2.Message}");
                    
                    // Attempt 3: Use reflection with ref parameter
                    object[] methodArgs = new object[1] { "" };
                    object reflectResult = ezcom.GetType().InvokeMember(
                        "File_GetDriveInformation",
                        System.Reflection.BindingFlags.InvokeMethod,
                        null,
                        ezcom,
                        methodArgs);
                    
                    errcd = Convert.ToInt32(reflectResult);
                    drive_info = methodArgs[0]?.ToString() ?? "";
                }
            }

            Console.WriteLine("   >>> STOP WIRESHARK CAPTURE <<<");
            Console.WriteLine();
            Console.WriteLine($"   Error Code: {errcd}");
            Console.WriteLine($"   Drive Info: '{drive_info}'");
            Console.WriteLine($"   Length: {drive_info.Length} bytes");

            if (errcd > 0)
            {
                Console.WriteLine($"   ✓ SUCCESS ({errcd} bytes returned)");
                Console.WriteLine();
                Console.WriteLine("   Hex Dump:");
                foreach (char c in drive_info)
                {
                    Console.Write($" {(int)c:X2}");
                }
                Console.WriteLine();
            }
            else if (errcd == 0)
            {
                Console.WriteLine("   ! No drives found (errcd=0)");
            }
            else
            {
                Console.WriteLine($"   ✗ ERROR: {errcd}");
            }

            // Step 6: Close (same as Python)
            Console.WriteLine();
            Console.WriteLine("6. Closing connection...");
            try
            {
                ezcom.Close();
                Console.WriteLine("   ✓ Closed");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"   Warning: {ex.Message}");
            }

            // Step 7: Release (same as Python)
            try
            {
                ezcom.Release();
                Console.WriteLine("   ✓ Released");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"   Warning: {ex.Message}");
            }

            Console.WriteLine();
            Console.WriteLine("Test completed successfully!");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: {ex.Message}");
            Console.WriteLine($"Type: {ex.GetType().Name}");
            if (ex is COMException comEx)
            {
                Console.WriteLine($"HRESULT: 0x{comEx.ErrorCode:X8}");
            }
        }

        Console.WriteLine();
        Console.WriteLine("Press Enter to exit...");
        Console.ReadLine();
    }
}
