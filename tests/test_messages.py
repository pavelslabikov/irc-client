import pytest
import irc.models.messages as msg
import irc.models.commands as com


@pytest.mark.parametrize(
    "message_type, raw_message, expected_result",
    [
        (
            msg.JoinMessage,
            ":nick!user JOIN :#channel",
            "nick присоединился к #channel",
        ),
        (
            msg.ModeMessage,
            ":bot!@service MODE #test -i",
            "bot!@service установил для #test флаг -i",
        ),
        (msg.ModeMessage, ":nick MODE nick -r", "nick сменил свой флаг на -r"),
        (
            msg.NickMessage,
            ":nick!0.0.0@user NICK new_nick1",
            "nick сменил ник на new_nick1",
        ),
        (
            msg.ServiceMessage,
            ":irc.ircnet.su 200 target :text",
            "[irc.ircnet.su] >> text",
        ),
        (
            msg.PrivateMessage,
            ":nick PRIVMSG target :test text",
            "[target] <nick>: test text",
        ),
    ],
)
def test_message_reg_exp(
    tested_client, message_type, raw_message: str, expected_result: str
):
    message = message_type(tested_client, raw_message)
    assert str(message) == expected_result


@pytest.mark.parametrize(
    "raw_data, expected_type",
    [
        (":bot!@service NOTICE target :text", msg.NoticeMessage),
        (":nick!user@1.1.1.1 JOIN :#channel", msg.JoinMessage),
        (":sender PRIVMSG target :text", msg.PrivateMessage),
        ("", None),
        ("unknown command", None),
    ],
)
def test_message_handler(tested_parser, raw_data: str, expected_type):
    for actual_message in tested_parser.get_messages(raw_data):
        assert isinstance(actual_message, expected_type)


@pytest.mark.parametrize(
    "error_response",
    [
        ":irc.ircnet.su 470 TestName :No such channel",
        ":irc.ircnet.su 442 TestName :You're not on that channel",
        ":irc.ircnet.su 471 TestName :Cannot join channel (+l)",
    ],
)
def test_channel_errors(tested_client, error_response: str):
    com.JoinCommand(tested_client, "#incorrect")()
    str(msg.ServiceMessage(tested_client, error_response))
    assert tested_client.current_channel is None
