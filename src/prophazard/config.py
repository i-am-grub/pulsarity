"""
Global configurations
"""

import logging
import asyncio
import datetime
from secrets import token_urlsafe
from typing import Literal

import anyio
import tomlkit

_DEFAULT_CONFIG_FILE_NAME = "config.toml"

_SECTIONS = Literal[
    "SECRETS",
    "WEBSERVER",
    "GENERAL",
]

_logger = logging.getLogger(__name__)
_file_lock = asyncio.Lock()


def _get_configs_defaults() -> dict[_SECTIONS, dict]:
    """
    Provides the server default configurations

    :return: The server defaults
    """

    # pylint: disable=R0915

    # secret configuration:
    secrets: dict = {}
    secrets["DEFAULT_USERNAME"] = "admin"
    secrets["DEFAULT_PASSWORD"] = "rotorhazard"
    secrets["SECRET_KEY"] = token_urlsafe(32)

    # webserver settings
    webserver: dict = {}
    webserver["HOST"] = "localhost"
    webserver["HTTP_PORT"] = 5000
    webserver["HTTPS_PORT"] = 5443
    webserver["FORCE_REDIRECTS"] = True
    webserver["KEY_FILE"] = "key.pem"
    webserver["KEY_PASSWORD"] = ""
    webserver["CERT_FILE"] = "cert.pem"
    webserver["CA_CERT_FILE"] = ""

    # other default configurations
    general: dict = {}
    general["DEBUG"] = False
    general["LAST_MODIFIED_TIME"] = 0

    config: dict[_SECTIONS, dict] = {
        "SECRETS": secrets,
        "WEBSERVER": webserver,
        "GENERAL": general,
    }

    return config


class ConfigManager:

    _configs: dict[_SECTIONS, dict] | None = None

    def __init__(self, filename: str) -> None:
        self._config_filename = filename

    def _write_file_config(self, configs_: dict[_SECTIONS, dict]):
        """
        Writes configs to a file synchronously. This should only be used before the
        webserver has been started.

        :param configs: Config dictionary to write
        :param filename: The file to save config to, defaults to _DEFAULT_CONFIG_FILE_NAME
        """
        configs_["GENERAL"]["LAST_MODIFIED_TIME"] = datetime.datetime.now()

        with open(self._config_filename, "w", encoding="utf-8") as file:
            file.write(tomlkit.dumps(configs_))

    async def _write_file_config_async(self, configs_: dict[_SECTIONS, dict]):
        """
        Writes configs to a file asynchronously. This should only be used after
        the webserver has started.

        :param configs: Config dictionary to write
        :param filename: The file to save config to, defaults to _DEFAULT_CONFIG_FILE_NAME
        """
        configs_["GENERAL"]["LAST_MODIFIED_TIME"] = datetime.datetime.now()

        async with _file_lock:
            async with await anyio.open_file(
                self._config_filename, "w", encoding="utf-8"
            ) as file:
                await file.write(tomlkit.dumps(configs_))

    def _load_config_from_file(self) -> dict[_SECTIONS, dict]:
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
            configs_ = _get_configs_defaults()
            self._write_file_config(configs_)
            return configs_

        except ValueError as ex:
            _logger.error(
                "Configuration file invalid, using defaults; error is: %s", ex
            )
            configs_ = _get_configs_defaults()
            self._write_file_config(configs_)
            return configs_

        return external_config

    def get_config(
        self,
        section: _SECTIONS,
        key: str,
    ) -> str | bool | int | float | None:
        """
        Gets a setting from the config file synchronously. This method
        of getting settings from the config file should be prefered
        before the webserver has started

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

    def set_config(self, section: _SECTIONS, key: str, value) -> None:
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

    async def get_sharable_config(self) -> dict[_SECTIONS, dict]:
        """
        Generates a copy of the config file with the `SECRETS`
        section cleared

        :return: An object storing the object configs
        """
        if self._configs is None:
            self._configs = self._load_config_from_file()

        del self._configs["SECRETS"]
        return self._configs


configs = ConfigManager(_DEFAULT_CONFIG_FILE_NAME)
