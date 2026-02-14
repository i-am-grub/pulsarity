"""
Validation Models for API
"""

from abc import ABC, abstractmethod
from typing import Annotated, Literal, Self, Union

from google.protobuf.message import Message  # type: ignore
from pydantic import UUID4, BaseModel, Field

from pulsarity._protobuf import http_pb2, websocket_pb2


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
    def model_validate_protobuf(cls, data: bytes) -> Self:
        """
        Generates a validation model from protobuf data
        """

    @abstractmethod
    def model_dump_protobuf(self) -> Message:
        """
        Converts the validation model to a protobuf message
        """


class StatusResponse(ProtocolBufferModel):
    """
    Basic Response with status
    """

    status: bool

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = http_pb2.StatusResponse.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        return http_pb2.StatusResponse(status=self.status)


class LoginRequest(ProtocolBufferModel):
    """
    Request to login to the server
    """

    username: str
    password: str

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = http_pb2.LoginRequest.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        return http_pb2.LoginRequest(username=self.username, password=self.password)


class LoginResponse(ProtocolBufferModel):
    """
    Request to login to the server
    """

    password_reset_required: bool

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = http_pb2.LoginResponse.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
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
    def model_validate_protobuf(cls, data: bytes):
        message = http_pb2.ResetPasswordRequest.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        return http_pb2.ResetPasswordRequest(
            old_password=self.old_password, new_password=self.new_password
        )


class _WSEvent(BaseModel):
    id: UUID4


class PilotAddEvent(_WSEvent):
    event_id: Literal[websocket_pb2.EVENT_PILOT_ADD]  # type: ignore


class PilotAlterEvent(_WSEvent):
    event_id: Literal[websocket_pb2.EVENT_PILOT_ALTER]  # type: ignore


WebsocketEvent = Annotated[
    Union[PilotAddEvent, PilotAlterEvent], Field(discriminator="event_id")
]
