import pytest

from quart.testing import WebsocketResponseError

from prophazard.extensions import RHApplication


# @pytest.mark.asyncio
# async def test_server_websocket_unauth(app: RHApplication):

#     client = app.test_client()

#     async with client.websocket("/ws/server") as test_websocket:

#         with pytest.raises(WebsocketResponseError) as error:
#             await test_websocket.receive_json()
#             assert error.response.status_code == 401
