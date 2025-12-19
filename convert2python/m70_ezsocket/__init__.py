"""
Mitsubishi CNC M70 EZSocket Python Library
A Python library for communicating with Mitsubishi CNC M70 series machines over Ethernet using the EZSocket protocol.
"""

from .typedef import *
from .m70_connection import M70Connection
from .m70_error import M70Error, M70ErrorCode
from .m70_log import M70Logger, M70LogConfig, M70LogLevel, M70LogTarget

__version__ = "1.0.0"
__author__ = "Converted from C to Python"
__all__ = [
    'M70Connection',
    'M70Error',
    'M70ErrorCode',
    'M70Logger',
    'M70LogConfig',
    'M70LogLevel',
    'M70LogTarget',
]
