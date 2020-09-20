import os
import errors
from client import Client
from configparser import ConfigParser

DEFAULT_CONFIG = {
    "Settings": {"nickname": "undefined", "codepage": "cp1251"},
    "Servers": {}
}


def check_config(config: ConfigParser):
    if not config.has_section("Settings") or not config.has_section("Servers"):
        raise errors.ConfigError(config)


if __name__ == "__main__":
    client_config = ConfigParser(allow_no_value=True)
    if not os.path.exists("config.ini"):
        with open("config.ini", "w") as file:
            client_config.read_dict(DEFAULT_CONFIG)
            client_config.write(file)
    client_config.read("config.ini")
    check_config(client_config)
    client = Client(client_config)
    client.start_client()
