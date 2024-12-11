"""
Global configurations
"""

import copy
import logging
import json
import time
import anyio
from asyncio import Lock

DEFAULT_CONFIG_FILE_NAME = "config.json"

logger = logging.getLogger(__name__)
_file_lock = Lock()


def get_configs_defaults() -> dict:
    config: dict[str, dict] = {
        "SECRETS": {},
        "GENERAL": {},
        "TIMING": {},
        "UI": {},
        "USER": {},
        "HARDWARE": {},
        "LED": {},
        "LOGGING": {},
        "SENSORS": {},
    }

    # LED strip configuration:
    config["LED"]["LED_COUNT"] = 0  # Number of LED pixels.
    config["LED"][
        "LED_GPIO"
    ] = 10  # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
    config["LED"][
        "LED_FREQ_HZ"
    ] = 800000  # LED signal frequency in hertz (usually 800khz)
    config["LED"]["LED_DMA"] = 10  # DMA channel to use for generating signal (try 10)
    config["LED"][
        "LED_INVERT"
    ] = False  # True to invert the signal (when using NPN transistor level shift)
    config["LED"]["LED_CHANNEL"] = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53
    config["LED"]["LED_STRIP"] = "GRB"  # Strip type and colour ordering
    config["LED"]["LED_ROWS"] = 1  # Number of rows in LED array
    config["LED"]["PANEL_ROTATE"] = 0
    config["LED"]["INVERTED_PANEL_ROWS"] = False
    config["LED"]["SERIAL_CTRLR_PORT"] = None  # Serial port for LED-controller module
    config["LED"][
        "SERIAL_CTRLR_BAUD"
    ] = 115200  # Serial baud rate for LED-controller module

    # LED effect configuration
    config["LED"]["ledEffects"] = ""
    config["LED"]["ledBrightness"] = 32
    config["LED"]["ledColorNodes"] = ""
    config["LED"]["ledColorFreqs"] = ""
    config["LED"]["ledColorMode"] = ""
    config["LED"]["seatColors"] = [
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
    config["VRX_CONTROL"] = {}
    config["VRX_CONTROL"]["HOST"] = "localhost"  # MQTT broker IP Address
    config["VRX_CONTROL"]["ENABLED"] = False
    config["VRX_CONTROL"]["OSD_LAP_HEADER"] = "L"

    # hardware default configurations
    config["HARDWARE"]["I2C_BUS"] = 1

    # other default configurations
    config["GENERAL"]["HOST"] = "0.0.0.0"
    config["GENERAL"]["HTTP_PORT"] = 5000
    config["GENERAL"]["ADMIN_USERNAME"] = "admin"
    config["GENERAL"]["ADMIN_PASSWORD"] = "rotorhazard"
    config["GENERAL"]["SECONDARIES"] = []
    config["GENERAL"]["SECONDARY_TIMEOUT"] = 300  # seconds
    config["GENERAL"]["DEBUG"] = False
    config["GENERAL"]["CORS_ALLOWED_HOSTS"] = "*"
    config["GENERAL"]["FORCE_S32_BPILL_FLAG"] = False
    config["GENERAL"]["DEF_NODE_FWUPDATE_URL"] = ""
    config["GENERAL"]["SHUTDOWN_BUTTON_GPIOPIN"] = 18
    config["GENERAL"]["SHUTDOWN_BUTTON_DELAYMS"] = 2500
    config["GENERAL"]["DB_AUTOBKP_NUM_KEEP"] = 30
    config["GENERAL"][
        "RACE_START_DELAY_EXTRA_SECS"
    ] = 0.9  # amount of extra time added to prestage time
    config["GENERAL"]["LOG_SENSORS_DATA_RATE"] = 300  # rate at which to log sensor data
    config["GENERAL"]["SERIAL_PORTS"] = []
    config["GENERAL"]["LAST_MODIFIED_TIME"] = 0

    # UI
    config["UI"]["timerName"] = "RotorHazard"
    config["UI"]["timerLogo"] = ""
    config["UI"]["hue_0"] = "212"
    config["UI"]["sat_0"] = "55"
    config["UI"]["lum_0_low"] = "29.2"
    config["UI"]["lum_0_high"] = "46.7"
    config["UI"]["contrast_0_low"] = "#ffffff"
    config["UI"]["contrast_0_high"] = "#ffffff"
    config["UI"]["hue_1"] = "25"
    config["UI"]["sat_1"] = "85.3"
    config["UI"]["lum_1_low"] = "37.6"
    config["UI"]["lum_1_high"] = "54.5"
    config["UI"]["contrast_1_low"] = "#ffffff"
    config["UI"]["contrast_1_high"] = "#000000"
    config["UI"]["currentLanguage"] = ""
    config["UI"]["timeFormat"] = "{m}:{s}.{d}"
    config["UI"]["timeFormatPhonetic"] = "{m} {s}.{d}"
    config["UI"]["pilotSort"] = "name"

    # timing
    config["TIMING"]["startThreshLowerAmount"] = "0"
    config["TIMING"]["startThreshLowerDuration"] = "0"
    config["TIMING"]["calibrationMode"] = 1
    config["TIMING"]["MinLapBehavior"] = 0

    # user-specified behavior
    config["USER"]["voiceCallouts"] = ""
    config["USER"]["actions"] = "[]"

    # logging defaults
    config["LOGGING"]["CONSOLE_LEVEL"] = "INFO"
    config["LOGGING"]["SYSLOG_LEVEL"] = "NONE"
    config["LOGGING"]["FILELOG_LEVEL"] = "INFO"
    config["LOGGING"]["FILELOG_NUM_KEEP"] = 30
    config["LOGGING"]["CONSOLE_STREAM"] = "stdout"

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
