"""
Validation Models for API
"""

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """
    Basic Response with status
    """

    status: bool


class LoginRequest(BaseModel):
    """
    Request to login to the server
    """

    username: str
    password: str


class LoginResponse(BaseResponse):
    """
    Request to login to the server
    """

    password_reset_required: bool | None = None


class ResetPasswordRequest(BaseModel):
    """
    Request to reset a user's password
    """

    old_password: str
    new_password: str
