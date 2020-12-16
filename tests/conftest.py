import pytest
import irc.commands as com
from irc.client import Client
from irc.handlers import CommandHandler, MessageHandler
from irc.cli.view import CliView


@pytest.fixture()
def tested_client() -> Client:
    client = Client("TestName", "cp866", set("fav_server"), CliView())
    client.is_connected = True
    client.hostname = "test_server"
    return client


@pytest.fixture()
def network_client() -> Client:
    client = Client("TestName", "cp866", set(), CliView())
    yield client
    com.ExitCommand(client)


@pytest.fixture()
def tested_handler(tested_client) -> CommandHandler:
    return CommandHandler(tested_client)


@pytest.fixture()
def tested_parser(tested_client) -> MessageHandler:
    return MessageHandler(tested_client)
