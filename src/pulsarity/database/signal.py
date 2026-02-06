"""
ORM classes for signal data
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Callable, Self, TypeVar

from pydantic import TypeAdapter
from tortoise import Model, fields
from tortoise.fields import BinaryField

from pulsarity.database._base import PulsarityBase as _PulsarityBase

if TYPE_CHECKING:
    from pulsarity.database.slot import Slot

# pylint: disable=R0903,E1136, E1101

_T = TypeVar("_T")
_SignalHistoryRecord = tuple[float, float]
_SLOT_HISTORY_ENCODE_ADAPTER = TypeAdapter(list[_SignalHistoryRecord])
_SLOT_HISTORY_DECODE_ADAPTER = TypeAdapter(tuple[_SignalHistoryRecord, ...])


class _EncodedBinaryField(BinaryField, fields.Field[_T]):  # type: ignore
    """
    Adaptation of the Binary field to enable automatic object encoding
    and decoding.

    Note that filter or queryset-update operations are not supported.
    """

    # pylint: disable=R0903,C0103

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
        value: _T,
        instance: type[Model] | Model,
    ) -> bytes:
        self.validate(value)
        return self.encoder(value)

    def to_python_value(self, value: bytes) -> _T:
        return self.decoder(value)


def _history_encoder(history_series: Sequence[_SignalHistoryRecord]) -> bytes:
    """
    Sorts and encodes a time series sequence to a storable binary value.

    :param history_series: The history series sequence
    :return: The formated time series
    """
    data = _SLOT_HISTORY_ENCODE_ADAPTER.validate_python(history_series)
    data.sort()
    return _SLOT_HISTORY_ENCODE_ADAPTER.dump_json(data)


class SignalHistory(_PulsarityBase):
    """
    Time series context for slot
    """

    slot: fields.ForeignKeyRelation[Slot] = fields.ForeignKeyField(
        "event.Slot", "history"
    )
    """The slot the history belongs to"""
    timer_identifier = fields.CharField(32)
    """Identifier of the signal's origin interface"""
    timer_index = fields.IntField()
    """The index of the timer the signal originated from"""
    history = _EncodedBinaryField[Sequence[_SignalHistoryRecord]](
        _history_encoder,
        _SLOT_HISTORY_DECODE_ADAPTER.validate_python,
    )
    """The series of history for the slot"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "slot_history"
        unique_together = (("slot", "timer_index"),)

    def __lt__(self, obj: Self) -> bool:
        """
        Less than operation definition. Allows for sorting instances by timer index.
        """
        return self.timer_index < obj.timer_index
