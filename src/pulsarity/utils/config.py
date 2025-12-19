"""
Global configurations
"""

import logging
from datetime import datetime
from functools import partial
from pathlib import Path
from secrets import token_urlsafe
from typing import Self

import anyio
from pydantic import BaseModel, Field, ValidationError

from pulsarity.utils.logging import generate_default_config

DEFAULT_CONFIG_FILE = Path("config.json")


_logger = logging.getLogger(__name__)


class _SecretsConfig(BaseModel):
    default_username: str = "admin"
    default_password: str = "pulsarity"
    secret_key: str = Field(default_factory=partial(token_urlsafe, 32))


class _WebserverConfig(BaseModel):
    host: str = "localhost"
    http_port: int = 5000
    https_port: int = 5443
    force_redirects: bool = True
    key_file: Path = Field(default_factory=partial(Path, "key.pem"))
    key_password: str | None = None
    cert_file: Path = Field(default_factory=partial(Path, "cert.pem"))
    ca_cert_file: Path | None = None


class _GeneralConfig(BaseModel):
    last_modified_time: datetime = Field(default_factory=datetime.now)


class _SystemDatabaseConfig(BaseModel):
    engine: str = "tortoise.backends.sqlite"
    credentials: dict = Field(
        default_factory=partial(dict, (("file_path", "system.db"),))
    )


class _EventDatabaseConfig(BaseModel):
    engine: str = "tortoise.backends.sqlite"
    credentials: dict = Field(
        default_factory=partial(dict, (("file_path", "event.db"),))
    )


class _DatabaseConfig(BaseModel):
    system_db: _SystemDatabaseConfig = Field(default_factory=_SystemDatabaseConfig)
    event_db: _EventDatabaseConfig = Field(default_factory=_EventDatabaseConfig)


class PulsarityConfig(BaseModel):
    """
    The server configs
    """

    secrets: _SecretsConfig | None = Field(default_factory=_SecretsConfig)
    webserver: _WebserverConfig = Field(default_factory=_WebserverConfig)
    general: _GeneralConfig = Field(default_factory=_GeneralConfig)
    database: _DatabaseConfig = Field(default_factory=_DatabaseConfig)
    logging: dict = Field(default_factory=generate_default_config)

    @classmethod
    def from_file(cls, filepath: Path) -> Self:
        """
        Loads a config from a filepath

        :param filepath: The filepath to load the config from
        """
        try:
            with filepath.open("rb") as file:
                return cls.model_validate_json(file.read())

        except ValidationError:
            _logger.error("Invalid server config file. Using defaults.")
            return cls()

        except FileNotFoundError:
            _logger.info("Config file not found. Loading defaults")
            return cls()

    def write_config_to_file(self, filepath: Path) -> None:
        """
        Writes the current config to a file

        :param filepath: The filepath to save the config to
        """
        self.general.last_modified_time = datetime.now()

        with filepath.open("w", encoding="utf-8") as file:
            file.write(self.model_dump_json(indent=4))

    async def write_config_to_file_async(self, filepath: Path) -> None:
        """
        Writes the current config to a file

        :param filepath: The filepath to save the config to
        """
        self.general.last_modified_time = datetime.now()

        async with await anyio.open_file(filepath, "w", encoding="utf-8") as file:
            await file.write(self.model_dump_json(indent=4))

    def get_sharable_config(self) -> Self:
        """
        Gets a shareable version of the config data
        """
        copy_ = self.model_copy()
        copy_.secrets = None
        copy_.webserver.key_password = ""
        return copy_
