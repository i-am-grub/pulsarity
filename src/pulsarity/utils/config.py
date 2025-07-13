"""
Global configurations
"""

import asyncio
import copy
import datetime
import logging
from secrets import token_urlsafe
from typing import Any, Literal

import anyio
import tomlkit

from pulsarity.utils.logging import generate_default_config

DEFAULT_CONFIG_FILE_NAME = "config.toml"

ConfigSections = Literal["SECRETS", "WEBSERVER", "GENERAL", "LOGGING", "DATABASE"]

_logger = logging.getLogger(__name__)


def get_configs_defaults() -> dict[ConfigSections, dict]:
    """
    Provides the server default configurations

    :return: The server defaults
    """

    # pylint: disable=R0915

    # secret configuration:
    secrets = {
        "DEFAULT_USERNAME": "admin",
        "DEFAULT_PASSWORD": "pulsarity",
        "SECRET_KEY": token_urlsafe(32),
    }

    # webserver settings
    webserver = {
        "HOST": "localhost",
        "HTTP_PORT": 5000,
        "HTTPS_PORT": 5443,
        "FORCE_REDIRECTS": True,
        "KEY_FILE": "key.pem",
        "KEY_PASSWORD": "",
        "CERT_FILE": "cert.pem",
        "CA_CERT_FILE": "",
        "API_DOCS": False,
    }

    # other default configurations
    general = {"LAST_MODIFIED_TIME": datetime.datetime.now()}

    # logging settings
    logging_ = generate_default_config()

    database = {
        "system_db": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {"file_path": "system.db"},
        },
        "event_db": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {"file_path": "event.db"},
        },
    }

    config: dict[ConfigSections, dict[str, Any]] = {
        "SECRETS": secrets,
        "WEBSERVER": webserver,
        "GENERAL": general,
        "LOGGING": logging_,
        "DATABASE": database,
    }

    return config


class ConfigManager:
    """
    Manager for dealing with the application config file
    """

    _configs: dict[ConfigSections, dict] | None = None

    def __init__(self, filename: str) -> None:
        self._config_filename = filename

    def _write_file_config(self, configs_: dict[ConfigSections, dict]):
        """
        Writes configs to a file synchronously. This should only be used before the
        webserver has been started.

        :param configs: Config dictionary to write
        :param filename: The file to save config to, defaults to _DEFAULT_CONFIG_FILE_NAME
        """
        configs_["GENERAL"]["LAST_MODIFIED_TIME"] = datetime.datetime.now()

        with open(self._config_filename, "w", encoding="utf-8") as file:
            file.write(tomlkit.dumps(configs_))

    async def _write_file_config_async(self, configs_: dict[ConfigSections, dict]):
        """
        Writes configs to a file asynchronously. This should only be used after
        the webserver has started.

        :param configs: Config dictionary to write
        :param filename: The file to save config to, defaults to _DEFAULT_CONFIG_FILE_NAME
        """
        configs_["GENERAL"]["LAST_MODIFIED_TIME"] = datetime.datetime.now()

        async with await anyio.open_file(
            self._config_filename, "w", encoding="utf-8"
        ) as file:
            await file.write(tomlkit.dumps(configs_))

    def _load_config_from_file(self) -> dict[ConfigSections, dict]:
        """
        Loads configs to a file synchronously. This should only be used before the
        webserver has been started.

        :param filename: The file to load the config from, defaults to _DEFAULT_CONFIG_FILE_NAME
        :return: The configuration settings
        """
        try:
            with open(self._config_filename, "r", encoding="utf-8") as file:
                external_config = tomlkit.load(file)

        except IOError:
            _logger.info("No configuration file found, using defaults")
            configs_ = get_configs_defaults()
            self._write_file_config(configs_)
            return configs_

        except ValueError as ex:
            _logger.error(
                "Configuration file invalid, using defaults; error is: %s", ex
            )
            configs_ = get_configs_defaults()
            self._write_file_config(configs_)
            return configs_

        return external_config.unwrap()  # type: ignore

    def get_config(
        self,
        section: ConfigSections,
        key: str,
    ) -> str | bool | int | float | None:
        """
        Gets a setting from the config file.

        :param section: The section in the config file for the setting
        :param key: The setting name
        :return: The setting value
        """
        if self._configs is None:
            self._configs = self._load_config_from_file()

        try:
            item = self._configs[section][key]
        except KeyError:
            return None

        return item

    def get_section(
        self,
        section: ConfigSections,
    ) -> dict[str, Any] | None:
        """
        Gets a section from the config file.

        :param section: The section in the config file for the setting
        :return: The setting value
        """
        if self._configs is None:
            self._configs = self._load_config_from_file()

        try:
            section_ = self._configs[section]
        except KeyError:
            return None

        return section_

    def set_config(self, section: ConfigSections, key: str, value) -> None:
        """
        Sets a setting from the config file asynchronously.

        :param section: The section in the config file for the setting
        :param key: The setting name
        :param value: The value to change the setting to
        """
        if self._configs is None:
            self._configs = self._load_config_from_file()

        self._configs[section][key] = value

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self._write_file_config(self._configs)
        else:
            loop.create_task(self._write_file_config_async(self._configs))

    def get_sharable_config(self) -> dict[ConfigSections, dict]:
        """
        Generates a copy of the config file with the `SECRETS`
        section cleared

        :return: An object storing the object configs
        """
        if self._configs is None:
            self._configs = self._load_config_from_file()

        configs_ = copy.copy(self._configs)

        del configs_["SECRETS"]
        return configs_


configs = ConfigManager(DEFAULT_CONFIG_FILE_NAME)
