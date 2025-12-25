"""
Validation Models for API
"""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """
    Model for parsing pagination parameters
    """

    cursor: int = Field(default=0, ge=0)
    limit: int = Field(default=10, gt=0, le=100)


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

    password_reset_required: bool


class ResetPasswordRequest(BaseModel):
    """
    Request to reset a user's password
    """

    old_password: str
    new_password: str
