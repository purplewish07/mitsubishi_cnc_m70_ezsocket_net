"""
Socket communication layer for M70 EZSocket
Converted from socket.h and socket.c
"""

import socket
import errno
from typing import Optional
from .m70_log import M70Logger


class M70Socket:
    """Socket communication wrapper"""
    
    @staticmethod
    def send_data(sock: socket.socket, data: bytes) -> int:
        """
        Send data through socket
        Returns: number of bytes sent, -1 on error
        """
        if sock is None:
            M70Logger.error("Send data failed: Invalid socket")
            return -1
        
        total_sent = 0
        data_length = len(data)
        
        while total_sent < data_length:
            try:
                sent = sock.send(data[total_sent:])
                if sent == 0:
                    M70Logger.error("Socket connection broken")
                    return -1
                total_sent += sent
                M70Logger.debug("Sent %d bytes of data, %d bytes remaining", 
                              sent, data_length - total_sent)
            except socket.error as e:
                if e.errno == errno.EINTR:
                    M70Logger.debug("Send data interrupted, continuing to try")
                    continue
                else:
                    M70Logger.error("Send data failed: %s (errno: %d)", str(e), e.errno)
                    return -1
        
        M70Logger.debug("Successfully sent all %d bytes of data", data_length)
        return total_sent
    
    @staticmethod
    def recv_data(sock: socket.socket, length: int) -> Optional[bytes]:
        """
        Receive data from socket
        Returns: received data bytes, None on error
        """
        if sock is None:
            M70Logger.error("Receive data failed: Invalid socket")
            return None
        
        data = bytearray()
        remaining = length
        
        while remaining > 0:
            try:
                chunk = sock.recv(remaining)
                if not chunk:
                    M70Logger.warning("Connection closed, received EOF")
                    break
                data.extend(chunk)
                remaining -= len(chunk)
                M70Logger.debug("Received %d bytes of data, %d bytes remaining", 
                              len(chunk), remaining)
            except socket.error as e:
                if e.errno == errno.EINTR:
                    M70Logger.debug("Receive data interrupted, continuing to try")
                    continue
                else:
                    M70Logger.error("Receive data failed: %s (errno: %s)", str(e), e.errno if e.errno is not None else "None")
                    return None
        
        M70Logger.debug("Successfully received %d bytes of data", len(data))
        return bytes(data)
    
    @staticmethod
    def recv_data_one_loop(sock: socket.socket, length: int) -> Optional[bytes]:
        """
        Receive data from socket in one loop (non-blocking receive)
        Returns: received data bytes, None on error
        """
        if sock is None:
            M70Logger.error("Receive data failed: Invalid socket")
            return None
        
        try:
            data = sock.recv(length)
            if not data:
                M70Logger.warning("Connection closed, received EOF")
                return None
            M70Logger.debug("Received %d bytes of data in one loop", len(data))
            return data
        except socket.error as e:
            M70Logger.error("Receive data failed: %s (errno: %d)", str(e), e.errno)
            return None
    
    @staticmethod
    def open_tcp_client_socket(ip: str, port: int) -> Optional[socket.socket]:
        """
        Open TCP client socket
        Returns: socket object, None on error
        """
        try:
            M70Logger.info("Opening TCP client socket to %s:%d", ip, port)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)  # 10 second timeout
            sock.connect((ip, port))
            M70Logger.info("Successfully connected to %s:%d", ip, port)
            return sock
        except socket.error as e:
            M70Logger.error("Failed to connect to %s:%d: %s", ip, port, str(e))
            return None
    
    @staticmethod
    def close_tcp_socket(sock: socket.socket):
        """Close TCP socket"""
        if sock:
            try:
                sock.close()
                M70Logger.debug("Socket closed successfully")
            except socket.error as e:
                M70Logger.error("Error closing socket: %s", str(e))
