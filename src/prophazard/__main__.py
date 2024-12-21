"""
PropHazard server entry point
"""

import sys
import multiprocessing
from . import prophazard_webserver

# pylint: disable=E0401

if sys.platform == "linux":
    multiprocessing.set_start_method("forkserver")
    from uvloop import run
elif sys.platform == "darwin":
    multiprocessing.set_start_method("spawn")
    from uvloop import run
elif sys.platform == "win32":
    multiprocessing.set_start_method("spawn")
    from winloop import run
else:
    multiprocessing.set_start_method("spawn")
    from asyncio import run


def main() -> None:
    """
    Run the PropHazard server
    """
    run(prophazard_webserver())


if __name__ == "__main__":
    main()
