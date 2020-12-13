import pytest
from irc.commands import ClientCommand
import irc.commands as com


@pytest.mark.parametrize(
    "test_input, expected_command",
    [
        ("", com.UnknownCommand),
        ("/list", com.ListCommand),
        ("/12345", com.UnknownCommand),
        ("/switch channel", com.SwitchCommand),
        ("/pm nick long test text", com.PrivateMessageCommand),
        ("/join #channel pass", com.JoinCommand),
        ("/chcp utf-8", com.CodePageCommand)
    ]
)
def test_command_handler(tested_handler, test_input: str, expected_command: ClientCommand):
    actual_command = tested_handler.get_command(test_input)
    assert isinstance(actual_command, expected_command)


@pytest.mark.parametrize(
    "command_type, expected_result, args",
    [
        (com.JoinCommand, "JOIN #casual \r\n", ("#casual",)),
        (com.JoinCommand, "JOIN &test pass\r\n", ("&test", "pass")),
        (com.NickCommand, "NICK new_nickname1\r\n", ("new_nickname1",)),
        (com.ConnectCommand, "", ("irc.ircnet.su", "6667")),
        (com.ListCommand, "LIST\r\n", ()),
        (com.PrivateMessageCommand, "PRIVMSG #channel :test text\r\n", ("#channel", "test", "text"))
    ]
)
def test_command_execution(tested_client, command_type, expected_result: str, args: tuple):
    actual_command = command_type(tested_client, *args)
    assert actual_command() == expected_result


@pytest.mark.parametrize(
    "command_type, expected_output, args",
    [
        (com.JoinCommand, "None", ("#casual",)),
        (com.ConnectCommand, "Вы уже подключены", ("irc.ircnet.su", "6667")),
        (com.NickCommand, "Недопустимый никнейм", ("!@^&$%",)),
        (com.AddToFavCommand, "Сервер test_server добавлен", ()),
        (com.CodePageCommand, "Допустимые кодировки:", ("cp1255",)),
        (com.PartCommand, "Вы не присоединены", ()),
        (com.SwitchCommand, "Вы не присоединены", ("#Channel",)),
        (com.HelpCommand, "| /add |", ()),
        (com.ShowFavCommand, "Список серверов", ())
    ]
)
def test_command_output(tested_client, command_type, expected_output: str, args: tuple):
    current_command = command_type(tested_client, *args)
    current_command()
    assert str(current_command.output).startswith(expected_output)

