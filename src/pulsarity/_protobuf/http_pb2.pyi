from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AuthenticatedResponse(_message.Message):
    __slots__ = ["status", "userinfo"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    USERINFO_FIELD_NUMBER: _ClassVar[int]
    status: bool
    userinfo: UserInfo
    def __init__(self, status: bool = ..., userinfo: _Optional[_Union[UserInfo, _Mapping]] = ...) -> None: ...

class LoginRequest(_message.Message):
    __slots__ = ["password", "username"]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    password: str
    username: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class LoginResponse(_message.Message):
    __slots__ = ["password_reset_required", "userinfo"]
    PASSWORD_RESET_REQUIRED_FIELD_NUMBER: _ClassVar[int]
    USERINFO_FIELD_NUMBER: _ClassVar[int]
    password_reset_required: bool
    userinfo: UserInfo
    def __init__(self, password_reset_required: bool = ..., userinfo: _Optional[_Union[UserInfo, _Mapping]] = ...) -> None: ...

class ResetPasswordRequest(_message.Message):
    __slots__ = ["new_password", "old_password"]
    NEW_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    OLD_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    new_password: str
    old_password: str
    def __init__(self, old_password: _Optional[str] = ..., new_password: _Optional[str] = ...) -> None: ...

class ServerData(_message.Message):
    __slots__ = ["server_name", "version"]
    SERVER_NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    server_name: str
    version: str
    def __init__(self, version: _Optional[str] = ..., server_name: _Optional[str] = ...) -> None: ...

class UserInfo(_message.Message):
    __slots__ = ["auth_id", "authenticated", "dispay_name", "permissions", "username"]
    AUTHENTICATED_FIELD_NUMBER: _ClassVar[int]
    AUTH_ID_FIELD_NUMBER: _ClassVar[int]
    DISPAY_NAME_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    auth_id: str
    authenticated: bool
    dispay_name: str
    permissions: _containers.RepeatedScalarFieldContainer[str]
    username: str
    def __init__(self, authenticated: bool = ..., auth_id: _Optional[str] = ..., username: _Optional[str] = ..., dispay_name: _Optional[str] = ..., permissions: _Optional[_Iterable[str]] = ...) -> None: ...
