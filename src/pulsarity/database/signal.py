"""
ORM classes for signal data
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from google.protobuf.message import Message
from tortoise import Model, fields

from pulsarity._protobuf import database_pb2
from pulsarity.database._base import PulsarityBase as _PulsarityBase

if TYPE_CHECKING:
    from pulsarity.database.slot import Slot


class ProtobufField[T: Message](fields.Field[T]):  # type: ignore
    """
    Protocol buffer field with automatic object encoding and decoding.

    Note that filter or queryset-update operations are not supported.
    """

    # pylint: disable=C0103

    __slots__ = ("message_type",)

    indexable = False
    SQL_TYPE = "BLOB"

    class _db_postgres:  # noqa: N801
        SQL_TYPE = "BYTEA"

    class _db_mysql:  # noqa: N801
        SQL_TYPE = "LONGBLOB"

    class _db_mssql:  # noqa: N801
        SQL_TYPE = "VARBINARY(MAX)"

    def __init__(
        self,
        message_type: type[T],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.message_type = message_type

    def to_db_value(
        self,
        value: T | bytes,
        instance: type[Model] | Model,  # noqa: ARG002
    ) -> bytes:
        if isinstance(value, bytes):
            return value
        return value.SerializeToString()

    def to_python_value(self, value: T | bytes) -> T:
        if isinstance(value, Message):
            return value
        return self.message_type.FromString(value)


class SignalHistory(_PulsarityBase):
    """
    Time series context for slot
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "slot_history"
        unique_together = (("slot", "timer_index"),)

    slot: fields.ForeignKeyRelation[Slot] = fields.ForeignKeyField(
        "event.Slot",
        "history",
    )
    """The slot the history belongs to"""
    timer_identifier = fields.CharField(32)
    """Identifier of the signal's origin interface"""
    timer_index = fields.IntField()
    """The index of the timer the signal originated from"""
    history = ProtobufField(database_pb2.SignalHistory)
    """The series of history for the slot"""

    def __lt__(self, obj: Self) -> bool:
        """
        Less than operation definition. Allows for sorting instances by timer index.
        """
        return self.timer_index < obj.timer_index
