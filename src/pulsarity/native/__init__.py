"""
Built-in Implementations
"""

import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def import_all_submodules() -> None:
    """
    Import all built-in implementation submodules
    """
    for file in Path(__file__).parent.iterdir():
        if file.name.isidentifier() and not file.name.startswith("_"):
            name = f"{__name__}.{file.name}"
            module = importlib.import_module(name)
            logger.debug("Imported model %s", module.__name__)
