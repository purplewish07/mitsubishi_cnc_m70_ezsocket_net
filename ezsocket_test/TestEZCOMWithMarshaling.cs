using System;
using System.Runtime.InteropServices;
using System.Text;

/// <summary>
/// Test with explicit COM marshaling for BSTR out parameters
/// Based on Python documentation: "client using VC++ needs to release string memory with CoTaskMemFree()"
/// </summary>
class TestEZCOMWithMarshaling
{
    // Import COM memory allocation functions
    [DllImport("ole32.dll")]
    static extern void CoTaskMemFree(IntPtr ptr);

    [DllImport("oleaut32.dll", PreserveSig = false)]
    static extern void SysReAllocString(ref IntPtr pbstr, [MarshalAs(UnmanagedType.LPWStr)] string psz);

    [DllImport("oleaut32.dll")]
    static extern void SysFreeString(IntPtr bstr);

    static void Main(string[] args)
    {
        Console.WriteLine("=== EZCOM Test with Explicit Marshaling ===");
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
            Console.WriteLine("1. Creating COM object...");
            Type ezcomType = Type.GetTypeFromProgID("EZNcAut.DispEZNcCommunication");
            if (ezcomType == null)
            {
                Console.WriteLine("ERROR: COM object not registered!");
                return;
            }
            object ezcom = Activator.CreateInstance(ezcomType);
            Console.WriteLine("   ✓ Created");

            // SetTCPIPProtocol
            Console.WriteLine($"2. SetTCPIPProtocol('{ip}', {port})...");
            object[] setTcpArgs = new object[] { ip, port };
            object setTcpResult = ezcomType.InvokeMember("SetTCPIPProtocol",
                System.Reflection.BindingFlags.InvokeMethod, null, ezcom, setTcpArgs);
            int errcd = Convert.ToInt32(setTcpResult);
            Console.WriteLine($"   Result: {errcd}");
            if (errcd != 0)
            {
                Console.WriteLine("   ERROR: Failed!");
                return;
            }

            // Open2
            Console.WriteLine("3. Open2(6, 1, 30, 'EZNC_LOCALHOST')...");
            object[] openArgs = new object[] { 6, 1, 30, "EZNC_LOCALHOST" };
            object openResult = ezcomType.InvokeMember("Open2",
                System.Reflection.BindingFlags.InvokeMethod, null, ezcom, openArgs);
            errcd = Convert.ToInt32(openResult);
            Console.WriteLine($"   Result: {errcd}");
            if (errcd != 0)
            {
                Console.WriteLine("   ERROR: Failed!");
                return;
            }
            Console.WriteLine("   ✓ Connected");
            Console.WriteLine();

            // File_GetDriveInformation with marshaling
            Console.WriteLine("4. File_GetDriveInformation()...");
            Console.WriteLine("   >>> START WIRESHARK CAPTURE NOW <<<");
            Console.WriteLine("   Press Enter...");
            Console.ReadLine();

            // Approach 1: Use VARIANT with VT_BSTR
            Console.WriteLine("   Approach 1: Using object array with empty string...");
            object[] methodArgs1 = new object[] { "" };
            object result1 = ezcomType.InvokeMember("File_GetDriveInformation",
                System.Reflection.BindingFlags.InvokeMethod, null, ezcom, methodArgs1);
            int errcd1 = Convert.ToInt32(result1);
            string driveInfo1 = methodArgs1[0]?.ToString() ?? "";
            Console.WriteLine($"   Result: errcd={errcd1}, data='{driveInfo1}', len={driveInfo1.Length}");
            Console.WriteLine();

            // Approach 2: Use StringBuilder
            Console.WriteLine("   Approach 2: Using StringBuilder (256 bytes buffer)...");
            StringBuilder sb = new StringBuilder(256);
            object[] methodArgs2 = new object[] { sb };
            object result2 = ezcomType.InvokeMember("File_GetDriveInformation",
                System.Reflection.BindingFlags.InvokeMethod, null, ezcom, methodArgs2);
            int errcd2 = Convert.ToInt32(result2);
            string driveInfo2 = methodArgs2[0]?.ToString() ?? "";
            Console.WriteLine($"   Result: errcd={errcd2}, data='{driveInfo2}', len={driveInfo2.Length}");
            Console.WriteLine();

            // Approach 3: Use null (let COM allocate)
            Console.WriteLine("   Approach 3: Using null (COM allocation)...");
            object[] methodArgs3 = new object[] { null };
            object result3 = ezcomType.InvokeMember("File_GetDriveInformation",
                System.Reflection.BindingFlags.InvokeMethod, null, ezcom, methodArgs3);
            int errcd3 = Convert.ToInt32(result3);
            string driveInfo3 = methodArgs3[0]?.ToString() ?? "";
            Console.WriteLine($"   Result: errcd={errcd3}, data='{driveInfo3}', len={driveInfo3.Length}");
            Console.WriteLine();

            // Approach 4: Pre-allocate large buffer
            Console.WriteLine("   Approach 4: Pre-allocated buffer (1024 chars)...");
            object[] methodArgs4 = new object[] { new string('\0', 1024) };
            object result4 = ezcomType.InvokeMember("File_GetDriveInformation",
                System.Reflection.BindingFlags.InvokeMethod, null, ezcom, methodArgs4);
            int errcd4 = Convert.ToInt32(result4);
            string driveInfo4 = methodArgs4[0]?.ToString() ?? "";
            // Trim null characters
            driveInfo4 = driveInfo4.TrimEnd('\0');
            Console.WriteLine($"   Result: errcd={errcd4}, data='{driveInfo4}', len={driveInfo4.Length}");
            Console.WriteLine();

            Console.WriteLine("   >>> STOP WIRESHARK CAPTURE <<<");
            Console.WriteLine();

            // Display best result
            if (!string.IsNullOrEmpty(driveInfo1))
            {
                Console.WriteLine($"SUCCESS: Approach 1 returned '{driveInfo1}'");
            }
            else if (!string.IsNullOrEmpty(driveInfo2))
            {
                Console.WriteLine($"SUCCESS: Approach 2 returned '{driveInfo2}'");
            }
            else if (!string.IsNullOrEmpty(driveInfo3))
            {
                Console.WriteLine($"SUCCESS: Approach 3 returned '{driveInfo3}'");
            }
            else if (!string.IsNullOrEmpty(driveInfo4))
            {
                Console.WriteLine($"SUCCESS: Approach 4 returned '{driveInfo4}'");
                DisplayHexDump(driveInfo4);
            }
            else
            {
                Console.WriteLine("FAILED: All approaches returned empty string");
            }

            // Close connection
            Console.WriteLine();
            Console.WriteLine("5. Closing...");
            ezcomType.InvokeMember("Close", System.Reflection.BindingFlags.InvokeMethod, null, ezcom, null);
            ezcomType.InvokeMember("Release", System.Reflection.BindingFlags.InvokeMethod, null, ezcom, null);
            Console.WriteLine("   ✓ Closed");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"EXCEPTION: {ex.Message}");
            Console.WriteLine($"Stack: {ex.StackTrace}");
            if (ex.InnerException != null)
            {
                Console.WriteLine($"Inner: {ex.InnerException.Message}");
            }
        }
    }

    static void DisplayHexDump(string data)
    {
        Console.WriteLine("   Hex Dump:");
        for (int i = 0; i < data.Length; i++)
        {
            if (i % 16 == 0)
            {
                Console.Write($"   {i:X4}: ");
            }
            Console.Write($"{(int)data[i]:X2} ");
            if ((i + 1) % 16 == 0 || i == data.Length - 1)
            {
                // Print ASCII representation
                Console.Write("  ");
                int start = (i / 16) * 16;
                for (int j = start; j <= i; j++)
                {
                    char c = data[j];
                    Console.Write(c >= 32 && c < 127 ? c : '.');
                }
                Console.WriteLine();
            }
        }
    }
}
