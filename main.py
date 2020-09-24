import os
from app import errors
from app.client import Client
from configparser import ConfigParser

DEFAULT_CONFIG = {
    "Settings": {"nickname": "undefined", "codepage": "cp1251"},
    "Servers": {}
}


def get_config() -> ConfigParser:
    current_config = ConfigParser(allow_no_value=True)
    if not os.path.exists("config/config.ini"):
        with open("config/config.ini", "w") as file:
            current_config.read_dict(DEFAULT_CONFIG)
            current_config.write(file)

    current_config.read("config/config.ini")
    if not current_config.has_section("Settings") or not current_config.has_section("Servers"):
        raise errors.ConfigError(current_config)
    return current_config


if __name__ == "__main__":
    try:
        client = Client(get_config())
        client.start_client()
    except errors.ApiError as e:
        print(e)
        exit()
    except Exception as e:
        print(f"{type(e)} : {str(e)}")
        exit()
