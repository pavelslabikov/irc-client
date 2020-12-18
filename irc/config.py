import os

from configparser import ConfigParser
from irc import const, errors
from irc.client import Client


class ClientConfig:
    @staticmethod
    def get_parser() -> ConfigParser:
        current_config = ConfigParser(allow_no_value=True)
        if not os.path.exists(const.CONFIG_PATH):
            raise errors.ConfigNotFoundError(os.getcwd())

        current_config.read(const.CONFIG_PATH)
        if not current_config.has_section(
            "Settings"
        ) or not current_config.has_section("Servers"):
            raise errors.InvalidConfigError(current_config)

        return current_config

    @staticmethod
    def refresh_file(client: Client):
        config = ClientConfig.get_parser()
        config["Settings"]["nickname"] = client.nickname
        config["Settings"]["codepage"] = client.code_page
        config["Servers"].update(client.favourites)
        if client.hostname in client.favourites:
            channels = ",".join(client.joined_channels)
            config["Servers"][client.hostname] = channels

        with open(const.CONFIG_PATH, "w") as file:
            config.write(file)
