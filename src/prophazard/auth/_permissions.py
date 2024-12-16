from enum import StrEnum, auto


class UserPermission(StrEnum):
    READ_PILOTS = auto()
    WRITE_PILOTS = auto()
