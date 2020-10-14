import os
import logging
from irc_client import errors, const
from irc_client.client import Client
from configparser import ConfigParser

logging.basicConfig(format="[%(levelname)s]: %(asctime)s | in %(name)s | %(message)s",
                    level=logging.DEBUG)


def get_config() -> ConfigParser:
    current_config = ConfigParser(allow_no_value=True)
    if not os.path.exists(const.CONFIG_PATH):
        raise errors.ConfigNotFoundError(os.getcwd())

    current_config.read(const.CONFIG_PATH)
    if not current_config.has_section("Settings") or not current_config.has_section("Servers"):
        raise errors.InvalidConfigError(current_config)

    return current_config


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    try:
        config = get_config()
        client = Client(config, config["Settings"]["nickname"], config["Settings"]["codepage"])
        logger.info("Starting client...")
        client.start_client()
    except errors.ApiError as e:
        logger.error(f"Client exception caught - {str(e)}")
    except Exception as e:
        logger.exception(f"Caught exception of type - {type(e)}:")
    finally:
        exit()
