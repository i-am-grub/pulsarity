"""
_summary_
"""

from enum import IntEnum


class HTTPStatusCodes(IntEnum):
    """
    Common HTTP status codes
    """

    OK = 200
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    UNSUPPORTED_MEDIA_TYPE = 415
    UNPROCESSABLE_CONTENT = 422
    INTERNAL_SERVER_ERROR = 500


class WebSocketStatusCodes(IntEnum):
    """
    Common Websocket status codes
    """

    NORMAL_CLOSURE = 1000
    GOING_AWAY = 1001
    INTERNAL_ERROR = 1011
    SERVICE_RESTART = 1012
