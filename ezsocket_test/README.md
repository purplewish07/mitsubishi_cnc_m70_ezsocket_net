# EZCOM GetDriveInformation Test

## 目的
測試 EZCOM COM API 的 `File_GetDriveInformation()` 方法，並通過 Wireshark 抓包分析是否使用 GIOP 協議。

## 重要說明

⚠️ **此測試需要 EZCOM.dll COM 組件**

如果您沒有 EZCOM.dll，有兩種替代方案：
1. **使用已安裝 EZCOM 的應用程序** - 在該應用中調用 GetDriveInformation，然後用 Wireshark 抓包
2. **使用我們已實現的 GIOP 方法** - 基於目錄探測的 GetDriveInformation（見下方）

## 前置需求

1. **安裝 EZCOM.dll**
   - 確保 EZCOM.dll 已安裝在系統中
   - 使用管理員權限註冊 COM：
     ```powershell
     # 以管理員身份運行 PowerShell
     regsvr32 "C:\path\to\EZCOM.dll"
     ```
   
   - 檢查是否已註冊：
     ```powershell
     Get-ChildItem REGISTRY::HKEY_CLASSES_ROOT\EZCOM.CncControl
     ```

2. **啟動 Wireshark**
   - 選擇網絡接口
   - 設置過濾器：`tcp.port == 683`
   - 開始捕獲

## 編譯和運行

### 方法 1：使用 dotnet CLI
```powershell
cd D:\test\mitsubishi_cnc_m70_ezsocket_net\convert2CSharp

# 編譯
dotnet build TestEZCOM.csproj

# 運行（使用默認 IP）
dotnet run --project TestEZCOM.csproj

# 運行（指定 IP 和 Port）
dotnet run --project TestEZCOM.csproj -- 192.168.1.137 683
```

### 方法 2：直接編譯 EXE
```powershell
cd D:\test\mitsubishi_cnc_m70_ezsocket_net\convert2CSharp
dotnet publish TestEZCOM.csproj -c Release -o ./bin/TestEZCOM
./bin/TestEZCOM/TestEZCOM.exe 192.168.1.137 683
```

## 使用步驟

1. **啟動 Wireshark 並開始捕獲**
2. **運行測試程序**
3. **程序會提示按 Enter 開始調用**
4. **按 Enter 後開始抓包**
5. **等待 GetDriveInformation 完成**
6. **停止 Wireshark 捕獲**

## 分析結果

### 如果看到 GIOP 封包：

查找包含以下特徵的封包：
- `GIOP 1.0 Request`
- Operation name 包含：
  - `mochaFSGetDriveInformation`
  - `mochaGetDriveInfo`
  - `Drive` 相關的字符串
- Reply 封包包含：
  - `M01:\r\n`
  - `M02:\r\n`
  - ASCII 字符 `4d 30 31 3a 0d 0a`

**結論**：✅ 可以通過 GIOP 實現

### 如果沒有 GIOP 封包：

- 沒有 GIOP 標識的封包
- 使用不同的 port
- 或完全沒有網絡通信（可能是本地 API）

**結論**：❌ 無法通過 GIOP 實現，需要使用 COM Interop

## 故障排除

### 錯誤：EZCOM.CncControl not registered
```
解決方案：
1. 找到 EZCOM.dll 文件
2. 以管理員身份運行：
   regsvr32 "C:\path\to\EZCOM.dll"
```

### 錯誤：Failed to connect
```
檢查：
1. CNC IP 地址是否正確
2. CNC 是否開機
3. 網絡連接是否正常
4. 防火牆是否阻擋 port 683
```

### 沒有 EZCOM.dll
```
替代方案：
1. 使用已有的 EZCOM 應用程序
2. 在該應用中調用 GetDriveInformation
3. 使用 Wireshark 抓包分析
```

## 預期輸出

如果成功，應該看到類似：
```
=== EZCOM GetDriveInformation Test ===
Target CNC: 192.168.1.137:683

✓ EZCOM object created successfully
Connecting to 192.168.1.137:683...
✓ Connected to CNC

Calling File_GetDriveInformation()...
>>> START CAPTURING PACKETS NOW <<<
Press Enter to continue...

>>> STOP CAPTURING PACKETS <<<

✓ GetDriveInformation succeeded!
Drive Info Length: 20 characters

Drive Information:
==================
M01:
M02:
M03:

==================

Hex dump:
4D 00 30 00 31 00 3A 00 0D 00 0A 00 4D 00 30 00 32 00 3A 00 0D 00 0A 00 ...
```

## 下一步

根據抓包結果：
1. ✅ **有 GIOP** → 分析 operation name，在 M70GIOP.cs 中實現
2. ❌ **無 GIOP** → 在 C# 中使用 COM Interop 直接調用 EZCOM.dll
