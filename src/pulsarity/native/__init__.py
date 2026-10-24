"""
Built-in Plugin Implementations

Note: The current architecture for the bundled plugins in this
module is not finalized.
"""

import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _import_submodules(name: str, path: Path) -> None:
    """
    Recursively import submodules
    """
    for path_ in path.iterdir():
        if (
            path_.is_file()
            and path_.stem.isidentifier()
            and not path_.stem.startswith("_")
            and path_.suffix == ".py"
        ):
            name_ = name + f".{path_.stem}"

            try:
                module = importlib.import_module(name_)
            except Exception:
                logger.exception("Error importing %s", name_)
            else:
                logger.debug("Imported module %s", module.__name__)

        elif (
            path_.is_dir()
            and path_.name.isidentifier()
            and not path_.name.startswith("_")
        ):
            name_ = name + f".{path_.name}"
            _import_submodules(name_, path_)


def import_all_submodules() -> None:
    """
    Import all built-in implementation submodules
    """
    _import_submodules(f"{__name__}", Path(__file__).parent)
