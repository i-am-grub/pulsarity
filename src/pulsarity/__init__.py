"""
A race timing and event management application built on asyncio
"""

from __future__ import annotations

import importlib.metadata

from packaging import version as _version

__version__ = importlib.metadata.version(__name__)
"""String representation of the server version"""
version = _version.parse(__version__)
"""Object representation of the server version"""
