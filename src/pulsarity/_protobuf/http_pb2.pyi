from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class LoginRequest(_message.Message):
    __slots__ = ["password", "username"]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    password: str
    username: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class LoginResponse(_message.Message):
    __slots__ = ["password_reset_required"]
    PASSWORD_RESET_REQUIRED_FIELD_NUMBER: _ClassVar[int]
    password_reset_required: bool
    def __init__(self, password_reset_required: bool = ...) -> None: ...

class ResetPasswordRequest(_message.Message):
    __slots__ = ["new_password", "old_password"]
    NEW_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    OLD_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    new_password: str
    old_password: str
    def __init__(self, old_password: _Optional[str] = ..., new_password: _Optional[str] = ...) -> None: ...

class StatusResponse(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: bool
    def __init__(self, status: bool = ...) -> None: ...
