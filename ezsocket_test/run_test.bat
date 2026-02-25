@echo off
echo ============================================
echo EZCOM GetDriveInformation Test
echo ============================================
echo.
echo Before running this test:
echo 1. Make sure EZCOM.dll is registered (regsvr32 EZCOM.dll)
echo 2. Start Wireshark and filter: tcp.port == 683
echo 3. The test will connect to CNC and call GetDriveInformation
echo.
echo Press any key to start...
pause > nul

dotnet run --project TestEZCOM.csproj -- 192.168.1.214 683

echo.
echo Test completed!
pause
