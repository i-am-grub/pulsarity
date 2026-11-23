from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UserInfo(_message.Message):
    __slots__ = ("authenticated", "auth_id", "username", "dispay_name", "permissions")
    AUTHENTICATED_FIELD_NUMBER: _ClassVar[int]
    AUTH_ID_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    DISPAY_NAME_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    authenticated: bool
    auth_id: str
    username: str
    dispay_name: str
    permissions: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, authenticated: _Optional[bool] = ..., auth_id: _Optional[str] = ..., username: _Optional[str] = ..., dispay_name: _Optional[str] = ..., permissions: _Optional[_Iterable[str]] = ...) -> None: ...

class AuthenticatedResponse(_message.Message):
    __slots__ = ("status", "userinfo")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    USERINFO_FIELD_NUMBER: _ClassVar[int]
    status: bool
    userinfo: UserInfo
    def __init__(self, status: _Optional[bool] = ..., userinfo: _Optional[_Union[UserInfo, _Mapping]] = ...) -> None: ...

class LoginRequest(_message.Message):
    __slots__ = ("username", "password")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    username: str
    password: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class LoginResponse(_message.Message):
    __slots__ = ("password_reset_required", "userinfo")
    PASSWORD_RESET_REQUIRED_FIELD_NUMBER: _ClassVar[int]
    USERINFO_FIELD_NUMBER: _ClassVar[int]
    password_reset_required: bool
    userinfo: UserInfo
    def __init__(self, password_reset_required: _Optional[bool] = ..., userinfo: _Optional[_Union[UserInfo, _Mapping]] = ...) -> None: ...

class ResetPasswordRequest(_message.Message):
    __slots__ = ("old_password", "new_password")
    OLD_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    NEW_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    old_password: str
    new_password: str
    def __init__(self, old_password: _Optional[str] = ..., new_password: _Optional[str] = ...) -> None: ...

class ServerData(_message.Message):
    __slots__ = ("version", "server_name", "language_version", "language_packs")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    SERVER_NAME_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_VERSION_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_PACKS_FIELD_NUMBER: _ClassVar[int]
    version: str
    server_name: str
    language_version: str
    language_packs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, version: _Optional[str] = ..., server_name: _Optional[str] = ..., language_version: _Optional[str] = ..., language_packs: _Optional[_Iterable[str]] = ...) -> None: ...

class LocalizationData(_message.Message):
    __slots__ = ("messages", "pluralization")
    class MessagesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class PluralizationEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    PLURALIZATION_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.ScalarMap[str, str]
    pluralization: _containers.ScalarMap[str, str]
    def __init__(self, messages: _Optional[_Mapping[str, str]] = ..., pluralization: _Optional[_Mapping[str, str]] = ...) -> None: ...
