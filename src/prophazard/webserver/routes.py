"""
HTTP Rest API Routes
"""

from quart import request

from .components import RHBlueprint

routes = RHBlueprint("routes", __name__)


@routes.get("/hello")
async def index():
    return {"hello": 0}


@routes.post("/echo")
async def echo():
    data = await request.get_json()
    return {"input": data, "extra": True}
