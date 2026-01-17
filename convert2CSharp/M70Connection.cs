using System.Net.Sockets;

namespace MitsubishiCncM70;

/// <summary>
/// M70 Connection class
/// Represents a connection to Mitsubishi CNC M70 series machine
/// </summary>
public class M70Connection : IDisposable
{
    private Socket? _socket;
    private bool _disposed;

    public bool IsConnected { get; private set; }
    public M70NCType NCType { get; private set; }
    public uint RequestId { get; set; }
    public bool IsLittleEndian { get; private set; }
    public string IpAddress { get; private set; } = string.Empty;
    public int Port { get; private set; }

    public M70Connection(string ipAddress, int port, M70NCType ncType = M70NCType.Meldas700M)
    {
        IpAddress = ipAddress;
        Port = port;
        NCType = ncType;
        IsLittleEndian = BitConverter.IsLittleEndian;
        RequestId = 0;
        IsConnected = false;
    }

    /// <summary>
    /// Connect to CNC machine
    /// </summary>
    public bool Connect()
    {
        try
        {
            _socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            _socket.Connect(IpAddress, Port);
            
            // Set socket options
            _socket.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReceiveTimeout, 5000);
            _socket.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.SendTimeout, 5000);
            _socket.SetSocketOption(SocketOptionLevel.Tcp, SocketOptionName.NoDelay, true);

            IsConnected = true;
            // Generate random request ID like Python version
            RequestId = (uint)Random.Shared.Next(0, 0xFFFF);
            
            return true;
        }
        catch
        {
            IsConnected = false;
            _socket?.Close();
            _socket = null;
            return false;
        }
    }

    /// <summary>
    /// Disconnect from CNC machine
    /// </summary>
    public void Disconnect()
    {
        if (_socket != null)
        {
            try
            {
                _socket.Shutdown(SocketShutdown.Both);
                _socket.Close();
            }
            catch { }
            finally
            {
                _socket = null;
                IsConnected = false;
            }
        }
    }

    /// <summary>
    /// Get the underlying socket
    /// </summary>
    internal Socket? GetSocket() => _socket;

    /// <summary>
    /// Send data to CNC
    /// </summary>
    internal int SendData(byte[] data)
    {
        if (_socket == null || !IsConnected)
            return -1;

        try
        {
            int totalSent = 0;
            while (totalSent < data.Length)
            {
                int sent = _socket.Send(data, totalSent, data.Length - totalSent, SocketFlags.None);
                if (sent <= 0)
                    return -1;
                totalSent += sent;
            }
            return totalSent;
        }
        catch
        {
            return -1;
        }
    }

    /// <summary>
    /// Receive data from CNC
    /// </summary>
    internal byte[]? ReceiveData(int length)
    {
        if (_socket == null || !IsConnected)
            return null;

        try
        {
            byte[] buffer = new byte[length];
            int totalReceived = 0;

            while (totalReceived < length)
            {
                int received = _socket.Receive(buffer, totalReceived, length - totalReceived, SocketFlags.None);
                if (received <= 0)
                    return null;
                totalReceived += received;
            }

            return buffer;
        }
        catch
        {
            return null;
        }
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            Disconnect();
            _disposed = true;
        }
        GC.SuppressFinalize(this);
    }

    ~M70Connection()
    {
        Dispose();
    }
}
