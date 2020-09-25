import socket
import threading
import re
from app.commands import ClientCommand
from configparser import ConfigParser

BUFFER_SIZE = 4096

MESSAGE_EXPR = re.compile(r":(?P<sender>[^\s!]+)(!.*)? (?P<command>PRIVMSG|NOTICE|\d{3}) (?P<target>.+) :(?P<text>.+)")
NOTIFICATION_EXPR = re.compile(r":(?P<nick>[^\s!]+)!?\S+ (?P<command>JOIN|PART|NICK|MODE).* :?(?P<target>\S+)")
SERVER_MSG_EXPR = re.compile(r":(?P<sender>\S+) (?P<command>\d{3}) \S+ (?P<text>.+) :")


class Client:
    def __init__(self, config: ConfigParser):
        self.sock = socket.socket()
        self.config = config
        self.nickname = config["Settings"]["nickname"]
        self.hostname = ""
        self.joined_channels = set()
        self.current_channel = ""
        self.is_connected = False
        self.is_working = True

    @property
    def cmd_prompt(self):
        if not self.current_channel:
            return f"<{self.nickname}>: "
        return f"[{self.current_channel}] <{self.nickname}>: "

    def start_client(self) -> None:
        input_thread = threading.Thread(target=self.wait_for_input)
        input_thread.start()
        self.wait_for_response()
        input_thread.join()

    def wait_for_input(self) -> None:
        parser = InputParser(self)
        while self.is_working:
            message = parser.parse_message(input(self.cmd_prompt)) + "\r\n"
            if self.is_connected:
                self.sock.sendall(bytes(message, "cp1251"))

    def wait_for_response(self) -> None:
        while self.is_working:
            while self.is_connected:
                data = self.sock.recv(BUFFER_SIZE)
                code_page = self.config["Settings"]["codepage"]
                print(Response(data, code_page))

    def refresh_config(self) -> None:
        with open("config/config.ini", "w") as file:
            self.config.write(file)


class InputParser:
    def __init__(self, client: Client):
        self.client = client
        cmd = ClientCommand(client)
        self.commands = {
            "/chcp": cmd.change_code_page,
            "/nick": cmd.change_nick,
            "/help": cmd.show_help,
            "/fav": cmd.show_favourites,
            "/server": cmd.connect,
            "/exit": cmd.exit_client
        }

        self.network_commands = {
            "/pm": cmd.send_personal_message,
            "/add": cmd.add_to_favourites,
            "/join": cmd.join_channel,
            "/list": cmd.show_channels,
            "/names": cmd.show_names,
            "/leave": cmd.leave_channel,
            "/quit": cmd.disconnect,
            "/switch": cmd.switch_channel
        }

    def parse_message(self, text: str) -> str:
        if text.startswith("/"):
            try:
                args = text.split(" ")
                result = ""
                cmd_name = args[0]
                cmd_args = args[1:]
                if cmd_name not in self.commands and cmd_name not in self.network_commands:
                    print("Неизвестная команда")
                if cmd_name in self.network_commands and self.client.is_connected:
                    result = self.network_commands[cmd_name](*cmd_args)
                if cmd_name in self.commands:
                    result = self.commands[cmd_name](*cmd_args)
                if result:
                    return result
            except TypeError:
                print(f"Неверное количество аргументов для команды: {cmd_name}")
        elif text.rstrip(" "):
            return f"PRIVMSG {self.client.current_channel} :{text}"

        return ""


class Response:
    COMMAND_REPR = {
        "JOIN": "joined",
        "PART": "left",
        "NICK": "is now known as",
        "MODE": "sets mode:"
    }

    def __init__(self, raw_response: bytes, code_page: str):
        self.decoded_data = raw_response.decode(code_page)

    def __str__(self) -> str:
        lines = self.decoded_data.split("\r\n")
        result = []
        for current_line in lines:
            for expr in [MESSAGE_EXPR, NOTIFICATION_EXPR, SERVER_MSG_EXPR]:
                match = expr.search(current_line)
                if match:
                    current_line = self.parse_match_obj(match, expr.pattern)
                    break
            result.append(current_line)
        return "\r\n".join(result)

    def parse_match_obj(self, expr: re.match, pattern: str) -> str:
        groups = expr.groupdict()
        if pattern == NOTIFICATION_EXPR.pattern:
            return f"<{groups['nick']}> {self.COMMAND_REPR[groups['command']]} {groups['target']}"

        if groups["command"] == "PRIVMSG":
            return f"[{groups['target']}] <{groups['sender']}>: {groups['text']}"

        return f"[{groups['sender']}] >> {groups['text']}"
