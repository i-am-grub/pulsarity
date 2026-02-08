"""
Validation Models for API
"""

from abc import ABC, abstractmethod
from typing import Self

from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel, Field

from pulsarity.protobuf import http_pb2


class PaginationParams(BaseModel):
    """
    Model for parsing pagination parameters
    """

    cursor: int = Field(default=0, ge=0)
    limit: int = Field(default=10, gt=0, le=100)


class LookupParams(BaseModel):
    """
    Model for parsing object id path params
    """

    id: int = Field(gt=0)


class ProtocolBufferModel(BaseModel, ABC):
    """
    Model defining Protocol Buffer compatibility
    """

    @classmethod
    @abstractmethod
    def from_protobuf(cls, data: bytes) -> Self:
        """
        Generates a validation model from protobuf data
        """

    @abstractmethod
    def to_message(self) -> Message:
        """
        Converts the validation model to a protobuf message
        """


class StatusResponse(ProtocolBufferModel):
    """
    Basic Response with status
    """

    status: bool

    @classmethod
    def from_protobuf(cls, data: bytes):
        message = http_pb2.StatusResponse.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def to_message(self):
        return http_pb2.StatusResponse(status=self.status)


class LoginRequest(ProtocolBufferModel):
    """
    Request to login to the server
    """

    username: str
    password: str

    @classmethod
    def from_protobuf(cls, data: bytes):
        message = http_pb2.LoginRequest.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def to_message(self):
        return http_pb2.LoginRequest(username=self.username, password=self.password)


class LoginResponse(ProtocolBufferModel):
    """
    Request to login to the server
    """

    password_reset_required: bool

    @classmethod
    def from_protobuf(cls, data: bytes):
        message = http_pb2.LoginResponse.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def to_message(self):
        return http_pb2.LoginResponse(
            password_reset_required=self.password_reset_required
        )


class ResetPasswordRequest(ProtocolBufferModel):
    """
    Request to reset a user's password
    """

    old_password: str
    new_password: str

    @classmethod
    def from_protobuf(cls, data: bytes):
        message = http_pb2.ResetPasswordRequest.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def to_message(self):
        return http_pb2.ResetPasswordRequest(
            old_password=self.old_password, new_password=self.new_password
        )
