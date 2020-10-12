import os
from irc_client import errors, const
from irc_client.client import Client
from configparser import ConfigParser


def get_config() -> ConfigParser:
    current_config = ConfigParser(allow_no_value=True)
    if not os.path.exists(const.CONFIG_PATH):
        raise errors.ConfigNotFoundError(const.CONFIG_PATH)

    current_config.read(const.CONFIG_PATH)
    if not current_config.has_section("Settings") or not current_config.has_section("Servers"):
        raise errors.InvalidConfigError(current_config)

    return current_config


if __name__ == "__main__":
    try:
        config = get_config()
        client = Client(config, config["Settings"]["nickname"], config["Settings"]["codepage"])
        client.start_client()
    except errors.ApiError as e:
        print(e)
    except Exception as e:
        print(f"{type(e)} : {str(e)}")
