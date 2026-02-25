# EZCOM COM API - GetDriveInformation Solution

## Problem
C# test returned error code 6 with empty string, while Python returned "M01:" successfully.

## Root Cause
**Method invocation issue**, not an actual error:

### ❌ Wrong Approach (Reflection)
```csharp
object[] methodArgs = new object[1];
object result = ezcom.GetType().InvokeMember(
    "File_GetDriveInformation",
    System.Reflection.BindingFlags.InvokeMethod,
    null, ezcom, methodArgs);
int errcd = Convert.ToInt32(result);  // Returns 6
string data = methodArgs[0]?.ToString() ?? "";  // Empty string
```

### ✅ Correct Approach (Dynamic)
```csharp
dynamic ezcom = Activator.CreateInstance(ezcomType);
string driveInfo = "";
int errcd = ezcom.File_GetDriveInformation(out driveInfo);
// errcd = 6 (bytes returned, not error!)
// driveInfo = "M01:\r\n"
```

## Key Findings

1. **Return Code 6 = Success**
   - NOT an error code
   - Indicates 6 bytes were returned
   - Data: `0x4D 0x30 0x31 0x3A 0x0D 0x0A` = "M01:\r\n"

2. **COM Interop Requirement**
   - Must use `dynamic` type, not reflection
   - Out parameters work correctly with dynamic binding
   - Reflection doesn't properly handle COM out parameters

3. **Drive Information Format**
   - Multiple drives: `"M01:\r\nM02:\r\n...M0N:\r\n\0"`
   - Each drive ends with CRLF (0x0D 0x0A)
   - Null-terminated string

## Working Test Results

```
Return Code: 6
Drive Info: 'M01:\n'
Length: 6 bytes
Hex Dump: 4D 30 31 3A 0D 0A (M01:\r\n)

Available Drives:
  - M01:

System_GetVersion Result:
  Version: 'BND-2007W000-D1  MITSUBISHI CNC 80M-A    BND-2800W000-24'
```

## Implementation Recommendation

For M70GIOP.cs, you have two options:

### Option 1: Use EZCOM COM API (Recommended)
```csharp
public List<string> GetDriveInformation()
{
    dynamic ezcom = CreateEZCOM();
    ezcom.SetTCPIPProtocol(ip, port);
    ezcom.Open2(6, unitNo, 30, "EZNC_LOCALHOST");
    
    string driveInfo = "";
    int result = ezcom.File_GetDriveInformation(out driveInfo);
    
    ezcom.Close();
    
    // Parse result
    return driveInfo.Split(new[] { "\r\n" }, StringSplitOptions.RemoveEmptyEntries)
                    .ToList();
}
```

### Option 2: Implement via GIOP (Needs Wireshark Analysis)
To implement using pure GIOP protocol:
1. Capture Wireshark packets during EZCOM call
2. Identify GIOP operation name (likely "melFsGetDriveInfo" or similar)
3. Analyze request/reply structure
4. Implement using existing MelGetData pattern

## Next Steps

1. **Wireshark Capture** (CRITICAL)
   - Run TestEZCOMWorking.csproj with Wireshark
   - Filter: `tcp.port == 683`
   - Analyze if GetDriveInformation uses GIOP internally
   
2. **If GIOP is used:**
   - Extract operation name from packet
   - Implement `MelFsGetDriveInformation()` in M70GIOP.cs
   - Use standard request/reply pattern
   
3. **If GIOP is NOT used:**
   - Use EZCOM COM wrapper in production code
   - Or implement directory probing fallback

## File Reference

- **Working Test**: `ezsocket_test/TestEZCOMWorking.cs`
- **Test Project**: `ezsocket_test/TestEZCOMWorking.csproj`
- **Python Reference**: See conversation (m700.py)
