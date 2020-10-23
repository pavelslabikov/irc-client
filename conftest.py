import pytest
import irc_client.commands as com
from irc_client.client import CommandHandler, Client, MessageHandler


@pytest.fixture()
def tested_client() -> Client:
    client = Client("TestName", "cp866", set("fav_server"))
    client.is_connected = True
    client.hostname = "test_server"
    return client


@pytest.fixture()
def network_client() -> Client:
    client = Client("TestName", "cp866", set())
    yield client
    com.ExitCommand(client)


@pytest.fixture()
def tested_handler(tested_client) -> CommandHandler:
    return CommandHandler(tested_client)


@pytest.fixture()
def tested_parser(tested_client) -> MessageHandler:
    return MessageHandler(tested_client)
