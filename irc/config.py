import os
from configparser import ConfigParser

from irc import const, errors


class ClientConfig:
    @staticmethod
    def get_from_file(path: str) -> ConfigParser:
        current_config = ConfigParser(allow_no_value=True)
        if not os.path.exists(path):
            raise errors.ConfigNotFoundError(os.getcwd())

        current_config.read(const.CONFIG_PATH)
        if not current_config.has_section("Settings") or not current_config.has_section("Servers"):
            raise errors.InvalidConfigError(current_config)

        return current_config
