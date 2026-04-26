"""
ORM classes for signal data
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Self, TypeVar

from google.protobuf.message import Message
from tortoise import Model, fields

from pulsarity._protobuf import database_pb2
from pulsarity.database._base import PulsarityBase as _PulsarityBase

if TYPE_CHECKING:
    from pulsarity.database.slot import Slot


_T = TypeVar("_T", bound=Message)


class _EncodedBinaryField(fields.Field[_T]):  # type: ignore
    """
    Adaptation of the Binary field to enable automatic object encoding
    and decoding.

    Note that filter or queryset-update operations are not supported.
    """

    # pylint: disable=C0103

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
        encoder: Callable[[_T], bytes],
        decoder: Callable[[bytes], _T],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.encoder = encoder
        self.decoder = decoder

    def to_db_value(
        self,
        value: _T | bytes,
        instance: type[Model] | Model,
    ) -> bytes:
        if isinstance(value, bytes):
            return value
        return self.encoder(value)

    def to_python_value(self, value: _T | bytes) -> _T:
        if isinstance(value, Message):
            return value
        return self.decoder(value)


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
        "event.Slot", "history"
    )
    """The slot the history belongs to"""
    timer_identifier = fields.CharField(32)
    """Identifier of the signal's origin interface"""
    timer_index = fields.IntField()
    """The index of the timer the signal originated from"""
    history = _EncodedBinaryField[database_pb2.SignalHistory](
        database_pb2.SignalHistory.SerializeToString,
        database_pb2.SignalHistory.FromString,
    )
    """The series of history for the slot"""

    def __lt__(self, obj: Self) -> bool:
        """
        Less than operation definition. Allows for sorting instances by timer index.
        """
        return self.timer_index < obj.timer_index
