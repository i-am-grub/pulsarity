from abc import ABC, abstractmethod
from datetime import datetime
from typing import Self

from google.protobuf import timestamp_pb2  # type: ignore
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel


def to_datetime(obj: timestamp_pb2.Timestamp | datetime) -> datetime:
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
