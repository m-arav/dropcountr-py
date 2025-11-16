"""
Dropcountr Python Client
~~~~~~~~~~~~~~~~~~~~~~~~~

A Python client library for the Dropcountr API.

Basic usage:

    >>> from dropcountr_client import DropcountrClient
    >>> with DropcountrClient(email="your@email.com", password="pass") as client:
    ...     client.login()
    ...     user_data = client.me()
    ...     print(user_data)

:copyright: (c) 2025
:license: MIT
"""

from .dropcountr_client import DropcountrClient

__version__ = "0.1.0"
__all__ = ["DropcountrClient"]

