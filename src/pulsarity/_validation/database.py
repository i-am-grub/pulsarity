"""
Validation classes for database data
"""

from datetime import datetime
from typing import Annotated, Iterable, Self

from google.protobuf import timestamp_pb2  # type: ignore
from pydantic import BeforeValidator, TypeAdapter

from pulsarity._protobuf import database_pb2
from pulsarity._validation._base import ProtocolBufferModel, to_datetime
from pulsarity.database.heat import Heat
from pulsarity.database.pilot import Pilot
from pulsarity.database.raceclass import RaceClass
from pulsarity.database.raceevent import RaceEvent
from pulsarity.database.round import Round


class AttributeModel(ProtocolBufferModel):
    """
    External attributes model
    """

    name: str

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = database_pb2.Attribute.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        message = database_pb2.Attribute(name=self.name)
        return message.SerializeToString()


class PilotModel(ProtocolBufferModel):
    """
    External Pilot model
    """

    id: int
    display_callsign: str
    display_name: str
    attributes: list[AttributeModel]

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = database_pb2.Pilot.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        attrs = (attribute.model_dump_protobuf() for attribute in self.attributes)
        return database_pb2.Pilot(
            id=self.id,
            display_callsign=self.display_callsign,
            display_name=self.display_callsign,
            attributes=attrs,
        )


_PILOTS_ADAPTER = TypeAdapter(list[PilotModel])


class PilotsModel(ProtocolBufferModel):
    """
    External Pilots model
    """

    pilots: list[PilotModel]

    @classmethod
    def from_iterable(cls, pilots: Iterable[Pilot]) -> Self:
        """
        Generates a validation model from a database iterable
        """
        return cls(pilots=_PILOTS_ADAPTER.validate_python(pilots, from_attributes=True))

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = database_pb2.Pilots.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        pilots = (pilot.model_dump_protobuf() for pilot in self.pilots)
        return database_pb2.Pilots(pilots=pilots)


class RaceEventModel(ProtocolBufferModel):
    """
    External event model
    """

    id: int
    name: str
    date: Annotated[datetime, BeforeValidator(to_datetime)]
    attributes: list[AttributeModel]

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.RaceEvent.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.RaceEvent:
        attrs = (attribute.model_dump_protobuf() for attribute in self.attributes)
        date = timestamp_pb2.Timestamp()
        date.FromDatetime(self.date)
        return database_pb2.RaceEvent(
            id=self.id, name=self.name, date=date, attributes=attrs
        )


_RACE_EVENTS_ADAPTER = TypeAdapter(list[RaceEventModel])


class RaceEventsModel(ProtocolBufferModel):
    """
    External events model
    """

    events: list[RaceEventModel]

    @classmethod
    def from_iterable(cls, events: Iterable[RaceEvent]) -> Self:
        """
        Generates a validation model from a database iterable
        """

        return cls(
            events=_RACE_EVENTS_ADAPTER.validate_python(events, from_attributes=True)
        )

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.RaceEvents.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.RaceEvents:
        events = (event.model_dump_protobuf() for event in self.events)
        return database_pb2.RaceEvents(events=events)


class RaceClassModel(ProtocolBufferModel):
    """
    External raceclass model
    """

    id: int
    name: str
    attributes: list[AttributeModel]

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.RaceClass.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.RaceClass:
        attrs = (attribute.model_dump_protobuf() for attribute in self.attributes)
        return database_pb2.RaceClass(id=self.id, name=self.name, attributes=attrs)


_RACE_CLASS_ADAPTER = TypeAdapter(list[RaceClassModel])


class RaceClassesModel(ProtocolBufferModel):
    """
    External raceclasses model
    """

    raceclasses: list[RaceClassModel]

    @classmethod
    def from_iterable(cls, raceclasses: Iterable[RaceClass]) -> Self:
        """
        Generates a validation model from a database iterable
        """
        return cls(
            raceclasses=_RACE_CLASS_ADAPTER.validate_python(
                raceclasses, from_attributes=True
            )
        )

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.RaceClasses.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.RaceClasses:
        raceclasses = (
            raceclass.model_dump_protobuf() for raceclass in self.raceclasses
        )
        return database_pb2.RaceClasses(raceclasses=raceclasses)


class RoundModel(ProtocolBufferModel):
    """
    External round model
    """

    id: int
    round_num: int
    attributes: list[AttributeModel]

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.Round.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.Round:
        attrs = (attribute.model_dump_protobuf() for attribute in self.attributes)
        return database_pb2.Round(
            id=self.id, round_num=self.round_num, attributes=attrs
        )


_RACE_ROUND_ADAPTER = TypeAdapter(list[RoundModel])


class RoundsModel(ProtocolBufferModel):
    """
    External rounds model
    """

    rounds: list[RoundModel]

    @classmethod
    def from_iterable(cls, rounds: Iterable[Round]) -> Self:
        """
        Generates a validation model from a database iterable
        """
        return cls(
            rounds=_RACE_ROUND_ADAPTER.validate_python(rounds, from_attributes=True)
        )

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.Rounds.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.Rounds:
        rounds = (round.model_dump_protobuf() for round in self.rounds)
        return database_pb2.Rounds(rounds=rounds)


class HeatModel(ProtocolBufferModel):
    """
    External heat model
    """

    id: int
    heat_num: int
    attributes: list[AttributeModel]

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = database_pb2.Heat.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        attrs = (attribute.model_dump_protobuf() for attribute in self.attributes)
        return database_pb2.Heat(id=self.id, heat_num=self.heat_num, attributes=attrs)


_RACE_HEAT_ADAPTER = TypeAdapter(list[HeatModel])


class HeatsModel(ProtocolBufferModel):
    """
    External heats model
    """

    heats: list[HeatModel]

    @classmethod
    def from_iterable(cls, heats: Iterable[Heat]) -> Self:
        """
        Generates a validation model from a database iterable
        """
        return cls(
            heats=_RACE_HEAT_ADAPTER.validate_python(heats, from_attributes=True)
        )

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.Heats.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.Heats:
        heats = (heat.model_dump_protobuf() for heat in self.heats)
        return database_pb2.Heats(heats=heats)
