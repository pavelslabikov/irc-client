import unittest
import configparser
import warnings
from irc_client import client as app, const


class TestResponseMethods(unittest.TestCase):
    def test_parsing_notifications(self):
        cases = {b":nick!user JOIN :#channel": "<nick> joined #channel",
                 b":nick!user NICK :other_nick1": "<nick> is now known as other_nick1",
                 b":nick!user PART :#chan": "<nick> left #chan",
                 b":bot!@service MODE :-i": "<bot> sets mode: -i"}
        for test_case, expected in cases.items():
            with self.subTest(test_case):
                response = app.Response(test_case, "cp1251")
                self.assertEqual(str(response), expected)

    def test_parsing_server_messages(self):
        cases = {b":irc.ircnet.su 100 target text :": "[irc.ircnet.su] >> text",
                 b":irc.ircnet.su NOTICE target :text": "[irc.ircnet.su] >> text",
                 b":irc.ircnet.su 200 target :text": "[irc.ircnet.su] >> text",
                 b":sender PRIVMSG target :text": "[target] <sender>: text",
                 b":bot!@service NOTICE target :text": "[bot] >> text"}
        for test_case, expected in cases.items():
            with self.subTest(test_case):
                response = app.Response(test_case, "cp1251")
                self.assertEqual(str(response), expected)


class TestInputParserMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        test_config = configparser.ConfigParser()
        test_config.read_dict(const.DEFAULT_CONFIG)
        client = app.Client(test_config)
        client.is_connected = True
        cls.parser = app.InputParser(client)
        warnings.simplefilter("ignore", ResourceWarning)
        super().setUpClass()

    def test_incorrect_commands(self):
        cases = ["/unknown 12345", "/123456", "/serverss",
                 "/", "/join", "/server 12345", "/nick !invalid"]
        for test_case in cases:
            with self.subTest(test_case):
                actual = self.parser.parse_message(test_case)
                self.assertEqual(actual, "")

    def test_basic_commands(self):
        cases = {"/names": f"NAMES ", "/list": "LIST",
                 "/join #Channel pass": "JOIN #channel pass", "/nick nickname": "NICK nickname",
                 "/leave": "PART #channel", "/pm target some text": "PRIVMSG target :some text"}
        for test_case, expected in cases.items():
            with self.subTest(test_case):
                actual = self.parser.parse_message(test_case)
                self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
