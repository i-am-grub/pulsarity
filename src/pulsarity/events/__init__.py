"""
System events
"""

from pulsarity.events.broker import EventBroker, register_as_callback
from pulsarity.events.enums import (
    EventSetupEvt,
    RaceSequenceEvt,
    SpecialEvt,
    _ApplicationEvt,
)

__all__ = [
    "EventBroker",
    "EventSetupEvt",
    "RaceSequenceEvt",
    "SpecialEvt",
    "_ApplicationEvt",
    "register_as_callback",
]
