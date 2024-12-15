"""
Global configurations
"""

import copy
import logging
import json
import time
import anyio
from secrets import token_urlsafe
from asyncio import Lock

DEFAULT_CONFIG_FILE_NAME = "config.json"

logger = logging.getLogger(__name__)
_file_lock = Lock()


def get_configs_defaults() -> dict[str, dict]:

    # secret configuration:
    secrets: dict = {}
    secrets["ADMIN_USERNAME"] = "admin"
    secrets["ADMIN_PASSWORD"] = "rotorhazard"
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

    # other default configurations
    general: dict = {}
    general["HOST"] = "0.0.0.0"
    general["HTTP_PORT"] = 5000
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

    config: dict[str, dict] = {
        "SECRETS": secrets,
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


def write_file_config(configs: dict, filename: str = DEFAULT_CONFIG_FILE_NAME):
    configs["GENERAL"]["LAST_MODIFIED_TIME"] = int(time.time())

    with open(filename, "w") as f:
        f.write(json.dumps(configs, indent=2))


def load_config_from_file(filename: str = DEFAULT_CONFIG_FILE_NAME) -> dict:
    try:
        with open(filename, "r") as f:
            external_config = json.load(f)

    except IOError:
        logger.info("No configuration file found, using defaults")
        configs = get_configs_defaults()
        write_file_config(configs)
        return configs

    except ValueError as ex:
        logger.error(f"Configuration file invalid, using defaults; error is: {ex}")
        configs = get_configs_defaults()
        write_file_config(configs)
        return configs

    else:
        return external_config


async def load_config_from_file_async(filename: str = DEFAULT_CONFIG_FILE_NAME) -> dict:
    try:
        async with _file_lock:
            async with await anyio.open_file(filename, "r") as f:
                content = await f.read()
                external_config = json.loads(content)

    except IOError:
        logger.info("No configuration file found, using defaults")
        configs = get_configs_defaults()
        await write_file_config_async(configs)
        return configs

    except ValueError as ex:
        logger.error(f"Configuration file invalid, using defaults; error is: {ex}")
        configs = get_configs_defaults()
        await write_file_config_async(configs)
        return configs

    else:
        return external_config


async def write_file_config_async(
    configs: dict, filename: str = DEFAULT_CONFIG_FILE_NAME
):
    configs["GENERAL"]["LAST_MODIFIED_TIME"] = int(time.time())

    async with _file_lock:
        async with await anyio.open_file(filename, "w") as f:
            await f.write(json.dumps(configs, indent=2))


def get_item_from_file(
    section: str, key: str, filename: str = DEFAULT_CONFIG_FILE_NAME
) -> str | bool | int | float | None:
    configs = load_config_from_file(filename)
    try:
        item = configs[section][key]
    except KeyError:
        return None
    else:
        return item


async def set_item_in_file(
    section: str, key: str, value, filename: str = DEFAULT_CONFIG_FILE_NAME
) -> bool:
    configs = await load_config_from_file_async(filename)
    try:
        configs[section][key] = value
        await write_file_config_async(configs, filename)
    except KeyError:
        return False
    else:
        return True


class Config:

    configs = None

    def __init__(self, filename=DEFAULT_CONFIG_FILE_NAME):
        self.filename = filename

    async def load_config_file(self):
        self.configs = await load_config_from_file_async(self.filename)

    def get_item(self, section, key):
        try:
            return self.configs[section][key]
        except KeyError:
            return False

    def get_item_int(self, section, key, default_value=0):
        try:
            val = self.configs[section][key]
            if val:
                return int(val)
            else:
                return default_value
        except KeyError:
            return default_value
        except ValueError:
            return default_value

    def get_section(self, section):
        try:
            return self.configs[section]
        except KeyError:
            return False

    async def set_item(self, section, key, value):
        try:
            self.configs[section][key] = value
            await write_file_config_async(self.configs, self.filename)
        except KeyError:
            return False
        return True

    def get_sharable_config(self):
        sharable_config = copy.deepcopy(self.configs)
        del sharable_config["SECRETS"]
        return sharable_config
