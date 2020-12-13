import logging
import threading

from irc.config import ClientConfig
from irc import errors, const
from irc.client import Client
from irc.cli.view import CliView

logging.basicConfig(level=logging.DEBUG)


def start_client():
    input_thread = threading.Thread(target=client.wait_for_response)
    input_thread.start()
    while client.is_working:
        client.process_user_input(input())
    input_thread.join()


def refresh_config() -> None:
    config["Settings"]["nickname"] = client.nickname
    config["Settings"]["codepage"] = client.code_page
    for server in client.favourites:
        config.set("Servers", server)

    with open(const.CONFIG_PATH, "w") as file:
        config.write(file)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    try:
        config = ClientConfig.get_from_file(const.CONFIG_PATH)
        client = Client(config["Settings"]["nickname"],
                        config["Settings"]["codepage"],
                        set(config["Servers"].keys()),
                        CliView())
        logger.info("Starting client...")
        start_client()
        refresh_config()
    except errors.ApiError as e:
        logger.error(f"Client exception caught - {str(e)}")
    except Exception as e:
        logger.exception(f"Caught exception of type - {type(e)}:")
    finally:
        exit()

