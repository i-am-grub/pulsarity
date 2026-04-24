"""
Global configurations
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import partial
from pathlib import Path
from secrets import token_urlsafe
from typing import Any, Self

import anyio

from pulsarity.utils.logging import generate_default_config

DEFAULT_CONFIG_FILE = Path("config.json")

# pylint: disable=E1134,R0902


logger = logging.getLogger(__name__)


def _parse_types(params: list[tuple[str, Any]]):
    vals = {}

    for key, val in params:
        if key.startswith("_"):
            continue
        if isinstance(val, Path):
            vals[key] = str(val)
        elif isinstance(val, datetime):
            vals[key] = val.isoformat()


@dataclass
class _SecretsConfig:
    default_username: str = "admin"
    default_password: str = "pulsarity"  # noqa: S105
    secret_key: str = field(default_factory=partial(token_urlsafe, 32))


@dataclass
class _WebserverConfig:
    host: str = "localhost"
    http_port: int = 5000
    https_port: int = 5443
    force_redirects: bool = False
    key_file: Path = field(default_factory=partial(Path, "key.pem"))
    key_password: str | None = None
    cert_file: Path = field(default_factory=partial(Path, "cert.pem"))
    ca_cert_file: Path | None = None

    def __post_init__(self):
        self.key_file = Path(self.key_file)
        self.cert_file = Path(self.cert_file)
        if self.ca_cert_file is not None:
            self.ca_cert_file = Path(self.ca_cert_file)


@dataclass
class _GeneralConfig:
    last_modified_time: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if isinstance(self.last_modified_time, str):
            self.last_modified_time = datetime.fromisoformat(self.last_modified_time)


@dataclass
class _SystemDatabaseConfig:
    engine: str = "tortoise.backends.sqlite"
    credentials: dict = field(
        default_factory=partial(dict, (("file_path", "system.db"),)),
    )


@dataclass
class _EventDatabaseConfig:
    engine: str = "tortoise.backends.sqlite"
    credentials: dict = field(
        default_factory=partial(dict, (("file_path", "event.db"),)),
    )


@dataclass
class _DatabaseConfig:
    system_db: _SystemDatabaseConfig = field(default_factory=_SystemDatabaseConfig)
    event_db: _EventDatabaseConfig = field(default_factory=_EventDatabaseConfig)

    def __post_init__(self):
        if isinstance(self.system_db, dict):
            self.system_db = _SystemDatabaseConfig(**self.system_db)
        if isinstance(self.system_db, dict):
            self.event_db = _EventDatabaseConfig(**self.event_db)

    def model_dump(self) -> dict:
        """
        Dumps the model to a dictionary
        """
        return asdict(self)


@dataclass
class PulsarityConfig:
    """
    The server configs
    """

    secrets: _SecretsConfig = field(default_factory=_SecretsConfig)
    webserver: _WebserverConfig = field(default_factory=_WebserverConfig)
    general: _GeneralConfig = field(default_factory=_GeneralConfig)
    database: _DatabaseConfig = field(default_factory=_DatabaseConfig)
    logging: dict = field(default_factory=generate_default_config)
    _lock: asyncio.locks.Lock = field(default_factory=asyncio.locks.Lock, init=False)
    _from_save: bool = field(default=False, init=False)

    def __post_init__(self):
        if isinstance(self.secrets, dict):
            self.secrets = _SecretsConfig(**self.secrets)
        if isinstance(self.webserver, dict):
            self.webserver = _WebserverConfig(**self.webserver)
        if isinstance(self.general, dict):
            self.general = _GeneralConfig(**self.general)
        if isinstance(self.database, dict):
            self.database = _DatabaseConfig(**self.database)

    @classmethod
    def from_file(cls, filepath: Path) -> Self:
        """
        Loads a config from a filepath

        :param filepath: The filepath to load the config from
        """
        try:
            with filepath.open("rb") as file:
                config = cls(**json.load(file))
                config.from_save = True
                return config

        except TypeError:
            logger.exception("Invalid server config file. Using defaults.")
            return cls()

        except FileNotFoundError:
            logger.info("Config file not found. Loading defaults")
            return cls()

    @property
    def from_save(self) -> bool:
        """
        Status of the config file loading from a previous config file
        """
        return self._from_save

    @from_save.setter
    def from_save(self, status: bool) -> None:
        """
        Status of the config file loading from a previous config file
        """
        self._from_save = status

    def write_config_to_file(self, filepath: Path = DEFAULT_CONFIG_FILE) -> None:
        """
        Writes the current config to a file

        :param filepath: The filepath to save the config to
        """
        self.general.last_modified_time = datetime.now()

        with filepath.open("w", encoding="utf-8") as file:
            json.dump(asdict(self, dict_factory=_parse_types), file, indent=4)

    async def write_config_to_file_async(
        self,
        filepath: Path = DEFAULT_CONFIG_FILE,
    ) -> None:
        """
        Writes the current config to a file

        :param filepath: The filepath to save the config to
        """
        async with self._lock:
            self.general.last_modified_time = datetime.now()

            async with await anyio.open_file(filepath, "w", encoding="utf-8") as file:
                await file.write(
                    json.dumps(asdict(self, dict_factory=_parse_types), indent=4)
                )


config_manager = PulsarityConfig.from_file(DEFAULT_CONFIG_FILE)
