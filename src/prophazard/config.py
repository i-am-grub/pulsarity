"""
Global configurations
"""

import logging
import json
import anyio
import asyncio
import datetime
from secrets import token_urlsafe

from typing import Literal

_DEFAULT_CONFIG_FILE_NAME = "config.json"

_logger = logging.getLogger(__name__)
_file_lock = asyncio.Lock()

_SECTIONS = Literal[
    "SECRETS",
    "WEBSERVER",
    "GENERAL",
    "TIMING",
    "UI",
    "USER",
    "HARDWARE",
    "LED",
    "LOGGING",
    "SENSORS",
    "VRX_CONTROL",
]


def _get_configs_defaults() -> dict[_SECTIONS, dict]:
    """
    Provides the server default configurations

    :return dict[_SECTIONS, dict]: The server defaults
    """

    # secret configuration:
    secrets: dict = {}
    secrets["DEFAULT_USERNAME"] = "admin"
    secrets["DEFAULT_PASSWORD"] = "rotorhazard"
    secrets["SECRET_KEY"] = token_urlsafe(32)

    # LED strip configuration:
    led: dict = {}
    led["LED_COUNT"] = 0  # Number of LED pixels.
    led["LED_GPIO"] = (
        10  # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
    )
    led["LED_FREQ_HZ"] = 800000  # LED signal frequency in hertz (usually 800khz)
    led["LED_DMA"] = 10  # DMA channel to use for generating signal (try 10)
    led["LED_INVERT"] = (
        False  # True to invert the signal (when using NPN transistor level shift)
    )
    led["LED_CHANNEL"] = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53
    led["LED_STRIP"] = "GRB"  # Strip type and colour ordering
    led["LED_ROWS"] = 1  # Number of rows in LED array
    led["PANEL_ROTATE"] = 0
    led["INVERTED_PANEL_ROWS"] = False
    led["SERIAL_CTRLR_PORT"] = None  # Serial port for LED-controller module
    led["SERIAL_CTRLR_BAUD"] = 115200  # Serial baud rate for LED-controller module

    # LED effect configuration
    led["ledEffects"] = ""
    led["ledBrightness"] = 32
    led["ledColorNodes"] = ""
    led["ledColorFreqs"] = ""
    led["ledColorMode"] = ""
    led["seatColors"] = [
        "#0022ff",  # Blue
        "#ff5500",  # Orange
        "#00ff22",  # Green
        "#ff0055",  # Magenta
        "#ddff00",  # Yellow
        "#7700ff",  # Purple
        "#00ffdd",  # Teal
        "#aaaaaa",  # White
    ]

    # Legacy Video Receiver Configuration (DEPRECATED)
    vrx: dict = {}
    vrx["HOST"] = "localhost"  # MQTT broker IP Address
    vrx["ENABLED"] = False
    vrx["OSD_LAP_HEADER"] = "L"

    # hardware default configurations
    hardware: dict = {}
    hardware["I2C_BUS"] = 1

    # webserver settings
    webserver: dict = {}
    webserver["HOST"] = "localhost"
    webserver["PORT"] = 5000
    webserver["USE_HTTPS"] = False
    webserver["KEY_FILE"] = "key.pem"
    webserver["KEY_PASSWORD"] = None
    webserver["CERT_FILE"] = "cert.pem"
    webserver["CA_CERT_FILE"] = None

    # other default configurations
    general: dict = {}
    general["SECONDARIES"] = []
    general["SECONDARY_TIMEOUT"] = 300  # seconds
    general["DEBUG"] = False
    general["CORS_ALLOWED_HOSTS"] = "*"
    general["FORCE_S32_BPILL_FLAG"] = False
    general["DEF_NODE_FWUPDATE_URL"] = ""
    general["SHUTDOWN_BUTTON_GPIOPIN"] = 18
    general["SHUTDOWN_BUTTON_DELAYMS"] = 2500
    general["DB_AUTOBKP_NUM_KEEP"] = 30
    general["RACE_START_DELAY_EXTRA_SECS"] = (
        0.9  # amount of extra time added to prestage time
    )
    general["LOG_SENSORS_DATA_RATE"] = 300  # rate at which to log sensor data
    general["SERIAL_PORTS"] = []
    general["LAST_MODIFIED_TIME"] = 0

    # UI
    ui: dict = {}
    ui["timerName"] = "RotorHazard"
    ui["timerLogo"] = ""
    ui["hue_0"] = "212"
    ui["sat_0"] = "55"
    ui["lum_0_low"] = "29.2"
    ui["lum_0_high"] = "46.7"
    ui["contrast_0_low"] = "#ffffff"
    ui["contrast_0_high"] = "#ffffff"
    ui["hue_1"] = "25"
    ui["sat_1"] = "85.3"
    ui["lum_1_low"] = "37.6"
    ui["lum_1_high"] = "54.5"
    ui["contrast_1_low"] = "#ffffff"
    ui["contrast_1_high"] = "#000000"
    ui["currentLanguage"] = ""
    ui["timeFormat"] = "{m}:{s}.{d}"
    ui["timeFormatPhonetic"] = "{m} {s}.{d}"
    ui["pilotSort"] = "name"

    # timing
    timing: dict = {}
    timing["startThreshLowerAmount"] = "0"
    timing["startThreshLowerDuration"] = "0"
    timing["calibrationMode"] = 1
    timing["MinLapBehavior"] = 0

    # user-specified behavior
    user: dict = {}
    user["voiceCallouts"] = ""
    user["actions"] = "[]"

    # logging defaults
    log: dict = {}
    log["CONSOLE_LEVEL"] = "INFO"
    log["SYSLOG_LEVEL"] = "NONE"
    log["FILELOG_LEVEL"] = "INFO"
    log["FILELOG_NUM_KEEP"] = 30
    log["CONSOLE_STREAM"] = "stdout"

    config: dict[_SECTIONS, dict] = {
        "SECRETS": secrets,
        "WEBSERVER": webserver,
        "GENERAL": general,
        "TIMING": timing,
        "UI": ui,
        "USER": user,
        "HARDWARE": hardware,
        "LED": led,
        "LOGGING": log,
        "SENSORS": {},
        "VRX_CONTROL": vrx,
    }

    return config


def _write_file_config(
    configs: dict[_SECTIONS, dict], filename: str = _DEFAULT_CONFIG_FILE_NAME
):
    """
    Writes configs to a file synchronously. This should only be used before the
    webserver has been started.

    :param dict configs: Config dictionary to write
    :param str filename: The file to save config to, defaults to _DEFAULT_CONFIG_FILE_NAME
    """
    configs["GENERAL"]["LAST_MODIFIED_TIME"] = datetime.datetime.now().isoformat()

    with open(filename, "w") as f:
        f.write(json.dumps(configs, indent=2))


async def _write_file_config_async(
    configs: dict[_SECTIONS, dict], filename: str = _DEFAULT_CONFIG_FILE_NAME
):
    """
    Writes configs to a file asynchronously. This should only be used after
    the webserver has started.

    :param dict[_SECTIONS, dict] configs: Config dictionary to write
    :param str filename: The file to save config to, defaults to _DEFAULT_CONFIG_FILE_NAME
    """
    configs["GENERAL"]["LAST_MODIFIED_TIME"] = datetime.datetime.now().isoformat()

    async with _file_lock:
        async with await anyio.open_file(filename, "w") as f:
            await f.write(json.dumps(configs, indent=2))


def _load_config_from_file(
    filename: str = _DEFAULT_CONFIG_FILE_NAME,
) -> dict[_SECTIONS, dict]:
    """
    Loads configs to a file synchronously. This should only be used before the
    webserver has been started.

    :param str filename: The file to load the config from, defaults to _DEFAULT_CONFIG_FILE_NAME
    :return dict[_SECTIONS, dict]: The configuration settings
    """
    try:
        with open(filename, "r") as f:
            external_config = json.load(f)

    except IOError:
        _logger.info("No configuration file found, using defaults")
        configs = _get_configs_defaults()
        _write_file_config(configs)
        return configs

    except ValueError as ex:
        _logger.error(f"Configuration file invalid, using defaults; error is: {ex}")
        configs = _get_configs_defaults()
        _write_file_config(configs)
        return configs

    else:
        return external_config


async def _load_config_from_file_async(
    filename: str = _DEFAULT_CONFIG_FILE_NAME,
) -> dict[_SECTIONS, dict]:
    """
    Loads configs to a file asynchronously. This should be used after the
    webserver has started.

    :param str filename: The file to load the config from, defaults to _DEFAULT_CONFIG_FILE_NAME
    :return dict[_SECTIONS, dict]: The configuration settings
    """
    try:
        async with _file_lock:
            async with await anyio.open_file(filename, "r") as f:
                content = await f.read()
                external_config = json.loads(content)

    except IOError:
        _logger.info("No configuration file found, using defaults")
        configs = _get_configs_defaults()
        await _write_file_config_async(configs)
        return configs

    except ValueError as ex:
        _logger.error(f"Configuration file invalid, using defaults; error is: {ex}")
        configs = _get_configs_defaults()
        await _write_file_config_async(configs)
        return configs

    else:
        return external_config


def get_config(
    section: _SECTIONS,
    key: str,
) -> str | bool | int | float | None:
    """
    Gets a setting from the config file synchronously. This method
    of getting settings from the config file should be prefered
    before the webserver has started

    :param _SECTIONS section: The section in the config file for the setting
    :param str key: The setting name
    :return str | bool | int | float | None: The setting value
    """

    configs = _load_config_from_file()
    try:
        item = configs[section][key]
    except KeyError:
        return None
    else:
        return item


async def get_config_async(
    section: _SECTIONS,
    key: str,
) -> str | bool | int | float | None:
    """
    Gets a setting from the config file asynchronously. This method
    of getting settings from the config file should be prefered
    once the webserver has started.

    :param _SECTIONS section: The section in the config file for the setting
    :param str key: The setting name
    :return str | bool | int | float | None: The setting value
    """
    configs = await _load_config_from_file_async()
    try:
        item = configs[section][key]
    except KeyError:
        return None
    else:
        return item


async def set_config_async(section: _SECTIONS, key: str, value) -> None:
    """
    Sets a setting from the config file asynchronously.

    :param _SECTIONS section: The section in the config file for the setting
    :param str key: The setting name
    :param _type_ value: The value to change the setting to
    """
    configs = await _load_config_from_file_async()
    configs[section][key] = value
    await _write_file_config_async(configs)


async def get_sharable_config() -> dict[_SECTIONS, dict]:
    """
    Generates a copy of the config file with the `SECRETS`
    section cleared

    :return dict[_SECTIONS, dict]: An object storing the object configs
    """

    sharable_config = await _load_config_from_file_async()
    sharable_config["SECRETS"] = {}
    return sharable_config
