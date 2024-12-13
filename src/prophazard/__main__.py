"""
PropHazard server entry point
"""

import sys
from . import prophazard_webserver

if sys.platform == "linux":
    from uvloop import run
elif sys.platform == "darwin":
    from uvloop import run
elif sys.platform == "win32":
    from winloop import run
else:
    from asyncio import run

run(prophazard_webserver())
