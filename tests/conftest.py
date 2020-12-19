import pytest

from irc.client import Client
from irc.handlers import CommandHandler, MessageHandler
from irc.cli.view import CliView


@pytest.fixture()
def tested_client() -> Client:
    client = Client("TestName", "cp866", {"fav_server": ""}, CliView())
    client.is_connected = True
    client.hostname = "test_server"
    client.current_channel = "#test"
    client.joined_channels.add("#test")
    return client


@pytest.fixture()
def network_client() -> Client:
    client = Client("TestName", "cp866", {}, CliView())
    yield client
    client.exit_client()


@pytest.fixture()
def tested_handler(tested_client) -> CommandHandler:
    return CommandHandler(tested_client)


@pytest.fixture()
def tested_parser(tested_client) -> MessageHandler:
    return MessageHandler(tested_client)
