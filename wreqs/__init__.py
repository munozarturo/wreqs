"""
wreqs: Simplified and enhanced request handling.

This module provides a wrapper around the requests library with additional
features such as automatic retries, session management, and improved error handling.

Main components:
- wreq: A context manager for making HTTP requests with retry capabilities.
- wreqs_session: A context manager for managing request sessions.
- RequestContext: The core class handling request execution and retries.
- configure_logger: A function to set up logging for the wreqs module.

Typical usage:

    from wreqs import wreq, wreqs_session
    from requests import Request

    with wreqs_session():
        req = Request('GET', 'https://api.example.com/data')
        with wreq(req) as response:
            print(response.json())

For more detailed information, refer to the documentation of each component.
"""

from .context import wreq, wreqs_session, RequestContext, configure_logger
from .error import RetryRequestError

__all__ = [
    "wreq",
    "wreqs_session",
    "RequestContext",
    "configure_logger",
    "RetryRequestError",
]

__version__ = "0.1.3"  # Update this with your current version

# Type hints for better IDE support
from typing import Callable, Optional
from requests import Request, Response, Session
