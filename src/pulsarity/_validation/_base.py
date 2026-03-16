"""
Validation helpers
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

from google.protobuf import timestamp_pb2  # type: ignore
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime

    from google.protobuf.message import Message  # type: ignore


def to_datetime(obj: timestamp_pb2.Timestamp | datetime) -> datetime:
    """
    Converts a protocol buffer timestamp to datetime
    """
    if isinstance(obj, timestamp_pb2.Timestamp):
        return obj.ToDatetime()
    return obj


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
