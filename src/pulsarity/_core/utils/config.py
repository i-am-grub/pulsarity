"""
Global configurations
"""

import asyncio
import datetime as dt
import json
import logging
import secrets
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, Self

import anyio

import pulsarity._core.utils.logging as plogging

DEFAULT_CONFIG_FILE = Path("config.json")


logger = logging.getLogger(__name__)


def _parse_types(params: list[tuple[str, Any]]):
    vals = {}

    for key, val in params:
        if key.startswith("_"):
            continue
        if isinstance(val, Path):
            vals[key] = str(val)
        elif isinstance(val, dt.datetime):
            vals[key] = val.isoformat()
        else:
            vals[key] = val

    return vals


@dataclass
class _SecretsConfig:
    default_username: str = "admin"
    default_password: str = "pulsarity"  # noqa: S105
    secret_key: str = field(default_factory=partial(secrets.token_urlsafe, 32))


@dataclass
class _WebserverConfig:
    host: str = "127.0.0.1"
    port: int = 5000
    key_file: Path | None = None
    key_password: str | None = None
    cert_file: Path | None = None
    ca_cert_file: Path | None = None
    origins: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.key_file = Path(self.key_file) if self.key_file is not None else None
        self.cert_file = Path(self.cert_file) if self.cert_file is not None else None
        self.ca_cert_file = (
            Path(self.ca_cert_file) if self.ca_cert_file is not None else None
        )

    @property
    def using_ssl(self):
        """
        Property defining if ssl is expected to be used based on the configuration file
        """
        return self.key_file is not None and self.cert_file is not None


@dataclass
class _GeneralConfig:
    server_name: str = "Pulsarity"
    debug: bool = False
    last_modified_time: dt.datetime = field(default_factory=dt.datetime.now)

    def __post_init__(self):
        if isinstance(self.last_modified_time, str):
            self.last_modified_time = dt.datetime.fromisoformat(self.last_modified_time)


@dataclass
class PulsarityConfig:
    """
    The server configs
    """

    secrets: _SecretsConfig = field(default_factory=_SecretsConfig)
    webserver: _WebserverConfig = field(default_factory=_WebserverConfig)
    general: _GeneralConfig = field(default_factory=_GeneralConfig)
    _lock: asyncio.locks.Lock = field(default_factory=asyncio.locks.Lock, init=False)
    _from_save: bool = field(default=False, init=False)

    def __post_init__(self):
        if isinstance(self.secrets, dict):
            self.secrets = _SecretsConfig(**self.secrets)
        if isinstance(self.webserver, dict):
            self.webserver = _WebserverConfig(**self.webserver)
        if isinstance(self.general, dict):
            self.general = _GeneralConfig(**self.general)

    @classmethod
    def from_file(cls, filepath: Path) -> Self:
        """
        Loads a config from a filepath

        :param filepath: The filepath to load the config from
        """
        try:
            with filepath.open("rb") as file:
                data = json.load(file)
                config = cls(**data)
                config.from_save = True
                return config

        except TypeError:
            logger.exception("Invalid server config file. Using defaults.")
            return cls()

        except FileNotFoundError:
            logger.info("Config file not found. Creating default and file.")
            config_file = cls()
            config_file.write_config_to_file()
            return config_file

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
        self.general.last_modified_time = dt.datetime.now(tz=dt.UTC)

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
            self.general.last_modified_time = dt.datetime.now(tz=dt.UTC)

            async with await anyio.open_file(filepath, "w", encoding="utf-8") as file:
                await file.write(
                    json.dumps(asdict(self, dict_factory=_parse_types), indent=4),
                )


def get_sqlite_config() -> dict:
    """
    Get the default database config for sqlite connections
    """
    return {
        "system_db": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {"file_path": "system.db"},
        },
        "event_db": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {"file_path": "event.db"},
        },
    }


def generate_logging_config(debug: bool) -> dict:
    """
    Generate the logging configuration
    """
    if debug:
        return plogging.generate_default_config("DEBUG")
    return plogging.generate_default_config("INFO")


config_manager = PulsarityConfig.from_file(DEFAULT_CONFIG_FILE)
