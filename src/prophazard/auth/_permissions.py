from enum import StrEnum, auto


class UserPermission(StrEnum):
    RESET_PASSWORD = auto()
    READ_PILOTS = auto()
    WRITE_PILOTS = auto()
