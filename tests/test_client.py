import pytest
from irc.client import Client
import irc.models.commands as com


def test_network_interaction(network_client: Client):
    com.ConnectCommand(network_client, "irc.ircnet.su")()
    assert network_client.is_connected
    assert network_client.hostname == "irc.ircnet.su"
    actual_response = network_client.sock.recv(1024)
    assert actual_response.startswith(b":irc.ircnet.su NOTICE AUTH")


@pytest.mark.parametrize("hostname", ["123456", "irc.ircnet"])
def test_incorrect_hostname(network_client: Client, hostname: str):
    command = com.ConnectCommand(network_client, hostname)
    command()
    assert not network_client.is_connected
    assert not network_client.hostname
    assert command.output.startswith("Не удалось подключиться")
    com.ExitCommand(network_client)()


def test_sending_input(tested_client: Client):
    try:
        tested_client.process_user_input("test_text")
    except OSError:
        assert True
    else:
        assert False
