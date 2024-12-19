"""
PropHazard server entry point
"""

import sys
import multiprocessing
from . import prophazard_webserver

if sys.platform == "linux":
    multiprocessing.set_start_method("forkserver")
    from uvloop import run
elif sys.platform == "darwin":
    multiprocessing.set_start_method("spawn")
    from uvloop import run
elif sys.platform == "win32":
    from winloop import run
else:
    multiprocessing.set_start_method("spawn")
    from asyncio import run

run(prophazard_webserver())
