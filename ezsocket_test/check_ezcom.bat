@echo off
echo ============================================
echo EZCOM Installation Check
echo ============================================
echo.

echo Checking if EZCOM.CncControl is registered...
echo.

powershell -Command "if (Test-Path 'REGISTRY::HKEY_CLASSES_ROOT\EZCOM.CncControl') { Write-Host 'SUCCESS: EZCOM.CncControl is registered' -ForegroundColor Green; Get-ItemProperty 'REGISTRY::HKEY_CLASSES_ROOT\EZCOM.CncControl' } else { Write-Host 'ERROR: EZCOM.CncControl NOT registered' -ForegroundColor Red; Write-Host ''; Write-Host 'To register EZCOM.dll:' -ForegroundColor Yellow; Write-Host '1. Find EZCOM.dll file' -ForegroundColor Yellow; Write-Host '2. Run as Administrator: regsvr32 \"C:\path\to\EZCOM.dll\"' -ForegroundColor Yellow }"

echo.
echo Searching for EZCOM.dll on system...
powershell -Command "Get-ChildItem -Path C:\ -Filter EZCOM.dll -Recurse -ErrorAction SilentlyContinue | Select-Object FullName, Length, LastWriteTime"

echo.
pause
