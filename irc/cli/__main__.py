import logging
import threading

from irc.config import ClientConfig
from irc import errors
from irc.client import Client
from irc.cli.view import CliView

logging.basicConfig(level=logging.ERROR)


def start_client() -> None:
    input_thread = threading.Thread(target=client.wait_for_response)
    input_thread.start()
    while client.is_working:
        client.process_user_input(input())
    input_thread.join()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    try:
        config = ClientConfig.get_parser()
        client = Client(
            config["Settings"]["nickname"],
            config["Settings"]["codepage"],
            dict(config["Servers"]),
            CliView(),
        )
        logger.info("Starting client...")
        start_client()
        ClientConfig.refresh_file(client)
    except errors.ApiError as e:
        logger.error(f"Client exception caught - {str(e)}")
    except Exception as e:
        logger.exception(f"Caught exception of type - {type(e)}:")
    finally:
        exit()
