"""
Dropcountr Python Client
~~~~~~~~~~~~~~~~~~~~~~~~~

A Python client library for the Dropcountr API.

Basic usage:

    >>> from dropcountr import DropcountrClient
    >>> with DropcountrClient(email="your@email.com", password="pass") as client:
    ...     client.login()
    ...     user = client.me()
    ...     print(user.name)

:copyright: (c) 2025
:license: MIT
"""

from .client import DropcountrClient
from . import models

__version__ = "0.3.1"
__all__ = ["DropcountrClient", "models"]
