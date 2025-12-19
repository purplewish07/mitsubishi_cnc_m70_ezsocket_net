"""
Error handling for M70 EZSocket
Converted from m70_error.h and m70_error.c
"""

from typing import Optional
from .typedef import M70ErrorCode


class M70Error(Exception):
    """Exception class for M70 errors"""
    
    def __init__(self, error_code: M70ErrorCode, message: str = ""):
        self.error_code = error_code
        self.message = message
        super().__init__(self.__str__())
    
    def __str__(self):
        return f"M70 Error {self.error_code.name}({self.error_code}): {self.message}"


class M70ErrorHandler:
    """Error handler for M70 operations"""
    
    _last_error: Optional[M70Error] = None
    
    @classmethod
    def set_error(cls, error_code: M70ErrorCode, message: str = ""):
        """Set the last error"""
        cls._last_error = M70Error(error_code, message)
    
    @classmethod
    def get_last_error(cls) -> Optional[M70Error]:
        """Get the last error"""
        return cls._last_error
    
    @classmethod
    def clear_error(cls):
        """Clear the last error"""
        cls._last_error = None
    
    @classmethod
    def has_error(cls) -> bool:
        """Check if there is an error"""
        return cls._last_error is not None
