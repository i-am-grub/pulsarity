"""
A race timing and event management application built on asyncio
"""

from __future__ import annotations

import importlib.metadata

import semver

__version__ = importlib.metadata.version(__name__)
"""String representation of the server version"""
version = semver.Version.parse(__version__)
"""Semver object representation of the server version"""
