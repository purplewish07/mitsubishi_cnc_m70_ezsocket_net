# Mitsubishi CNC M70 EZSocket Library for C#

C#版本的三菱CNC M70系列通信库，支持通过EZSocket协议进行以太网通信。

## 🎯 特性

- ✅ 完整的文件系统操作（读取、写入、删除、列表）
- ✅ 高级API封装（类似Python版本）
- ✅ 低级GIOP协议访问
- ✅ 异步支持（可选）
- ✅ 类型安全
- ✅ 资源自动管理（IDisposable）
- ✅ .NET 8.0 支持

## 📦 项目结构

```
convert2CSharp/
├── MitsubishiCncM70.csproj  # 项目文件
├── TypeDef.cs               # 类型定义和枚举
├── M70Connection.cs         # 连接管理
├── M70GIOP.cs              # GIOP协议层（低级API）
├── M70EZSocket.cs          # 业务层（高级API）
├── Examples.cs             # 使用示例
└── README.md               # 本文档
```

## 🚀 快速开始

### 1. 构建项目

```bash
cd convert2CSharp
dotnet build
```

### 2. 基本用法

#### 下载文件

```csharp
using MitsubishiCncM70;

using var conn = new M70Connection("192.168.1.206", 683, M70NCType.Meldas700M);
if (conn.Connect())
{
    var result = M70EZSocket.DownloadFile(
        conn,
        @"M01:\PRG\USER\O3000.NC",
        "downloaded_O3000.NC"
    );
    
    if (result == M70ErrorCode.OK)
        Console.WriteLine("下载成功");
    
    conn.Disconnect();
}
```

#### 上传文件

```csharp
using var conn = new M70Connection("192.168.1.206", 683);
if (conn.Connect())
{
    var result = M70EZSocket.UploadFile(
        conn,
        "O3001.NC",                    // 本地文件
        @"M01:\PRG\USER\O3001.NC",    // CNC路径
        overwrite: true
    );
    
    if (result == M70ErrorCode.OK)
        Console.WriteLine("上传成功");
}
```

#### 列出目录

```csharp
using var conn = new M70Connection("192.168.1.206", 683);
if (conn.Connect())
{
    var (errorCode, files) = M70EZSocket.ListDirectory(
        conn,
        @"M01:\PRG\USER"
    );
    
    if (errorCode == M70ErrorCode.OK && files != null)
    {
        foreach (var file in files)
            Console.WriteLine(file);
    }
}
```

#### 删除文件

```csharp
using var conn = new M70Connection("192.168.1.206", 683);
if (conn.Connect())
{
    var result = M70EZSocket.DeleteFile(
        conn,
        @"M01:\PRG\USER\O3001.NC"
    );
    
    if (result == M70ErrorCode.OK)
        Console.WriteLine("删除成功");
}
```

## 📚 API 文档

### 高级API（M70EZSocket）

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `ReadFile` | 读取CNC上的文件 | `(M70ErrorCode, byte[]?)` |
| `WriteFile` | 写入文件到CNC | `M70ErrorCode` |
| `DeleteFile` | 删除CNC上的文件 | `M70ErrorCode` |
| `StatFile` | 获取文件信息 | `(M70ErrorCode, FileStatInfo?)` |
| `ListDirectory` | 列出目录内容（含详细信息） | `(M70ErrorCode, List<Dictionary<string,object>>?)` |
| `DownloadFile` | 下载文件到本地 | `M70ErrorCode` |
| `UploadFile` | 上传本地文件到CNC | `M70ErrorCode` |
| `ReadMainProgramName` | 读取主程序名称 | `(M70ErrorCode, string)` |
| `ReadMachineType` | 读取机械类型 | `(M70ErrorCode, M70NCMachineType)` |
| `GetDriveInformation` | 获取驱动器信息 | `(M70ErrorCode, List<string>?)` |

### 低级API（M70GIOP）

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `MelFsOpenFile` | 打开文件 | `(int errorCode, int fd)` |
| `MelFsReadFile` | 读取文件数据 | `(int, int, byte[]?)` |
| `MelFsCloseFile` | 关闭文件 | `int` |
| `MelFsCreateFile` | 创建新文件 | `(int, int)` |
| `MelFsWriteFile` | 写入文件数据 | `(int, int)` |
| `MelFsRemoveFile` | 删除文件 | `int` |
| `MelFsStatFile` | 获取文件状态 | `(int, FileStatInfo?)` |
| `MelFsOpenDirectory` | 打开目录 | `(int, int)` |
| `MelFsReadDirectory` | 读取目录项 | `(int, string?)` |
| `MelFsCloseDirectory` | 关闭目录 | `int` |
| `MelFsGetDriveInformation` | 获取驱动器信息 | `(int, string?)` |
| `MelGetData` | 通用数据读取 | `(int, object?)` |

## 🔧 系统要求

- .NET 8.0 或更高版本
- Windows / Linux / macOS

## 📝 路径格式

CNC路径使用以下格式：

```
M01:\PRG\USER\O3000.NC      # 用户程序目录
M01:\PRG\USER\LIBRARY\      # 用户子程序库
```

**注意事项：**
- 使用反斜杠 `\` 而非正斜杠 `/`
- 某些程序号可能被CNC系统保留（如O3000）
- 建议使用未被占用的程序号（如O3001、O9999）

## 🔄 与其他版本对比

### vs C版本
- ✅ 更安全（自动内存管理）
- ✅ 更易用（高级API封装）
- ✅ 类型安全（编译时检查）
- ✅ 异常处理更优雅
- ⚠️ 需要.NET运行时

### vs Python版本
- ✅ 性能提升 10-50倍
- ✅ 类型安全（静态类型）
- ✅ 更适合生产环境
- ✅ 更好的IDE支持
- ⚠️ 代码稍微冗长

## 🛠️ 开发

### 编译

```bash
dotnet build
```

### 测试

```bash
dotnet run --project Examples.cs
```

### 发布

```bash
# 单文件发布（包含运行时）
dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true

# 或框架依赖发布（需要安装.NET）
dotnet publish -c Release
```

## 📋 错误码

| 错误码 | 说明 |
|--------|------|
| `0x00` | 成功 |
| `0x80070002` | 文件不存在 |
| `0x80070142` | 无法打开文件 |
| `0x80070392` | 文件已存在 |
| `0x80070393` | 无法创建文件 |

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

与原C版本相同

## 🔗 相关项目

- C版本: `mitsubishi_cnc_m70_ezsocket_net/` (主分支)
- Python版本: `convert2python/` (convert2python分支)
- C#版本: `convert2CSharp/` (convert2CSharp分支)

## � 更新记录

### 2026-02-25
- ✅ 新增 `ReadMainProgramName` 方法，支持读取主程序名称
- ✅ 新增 `ReadMachineType` 方法，支持读取CNC机械类型（MC/车床）
- ✅ 增强 `ListDirectory` 方法，现在返回详细文件信息（大小、日期、注释等）
- ✅ 新增 `GetDriveInformation` 方法，通过GIOP协议获取驱动器列表
- ✅ 完善文件状态解析，修复时间字段对齐问题
- ✅ 改进示例程序，增加机械类型和驱动器信息显示
- 🔧 修复M70GIOP.cs中文件统计信息的字节对齐问题
- 🔧 优化错误处理和异常管理

## �📧 联系方式

有问题请提交Issue或联系原作者。
