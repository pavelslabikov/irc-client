import socket
import threading
import re
from commands import ClientCommand
from configparser import ConfigParser

CHUNK_SIZE = 2048
MESSAGE_EXPR = re.compile(r":(?P<sender>[^\s!]+)(!.*)? (?P<command>PRIVMSG|NOTICE|\d{3}) (?P<target>.+) :(?P<text>.+)")
NOTIFICATION_EXPR = re.compile(r":(?P<nick>[^\s!]+)!?\S+ (?P<command>JOIN|PART|NICK|MODE).* :?(?P<target>\S+)")
SERVER_MSG_EXPR = re.compile(r":(?P<sender>\S+) (?P<command>\d{3}) \S+ (?P<text>.+) :")


class Client:
    def __init__(self, config: ConfigParser):
        self.sock = socket.socket()
        self.config = config
        self.nickname = config["Settings"]["nickname"]
        self.code_page = config["Settings"]["codepage"]
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
        input_thread.daemon = True
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
                data = self.sock.recv(CHUNK_SIZE)
                print(str(Response(data, self.code_page)))

    def refresh_config(self) -> None:
        with open("config.ini", "w") as file:
            self.config.write(file)


class InputParser:
    def __init__(self, client: Client):
        self.client = client
        cmd = ClientCommand(client)
        self.commands = {
            "/bs": cmd.send_to_bot_service,
            "/cs": cmd.send_to_chan_service,
            "/ns": cmd.send_to_nick_service,
            "/chcp": cmd.change_code_page,
            "/nick": cmd.change_nick,
            "/add": cmd.add_to_favourites,
            "/fav": cmd.show_favourites,
            "/join": cmd.join_channel,
            "/list": cmd.show_channels,
            "/server": cmd.connect,
            "/names": cmd.show_names,
            "/switch": cmd.switch_channel,
            "/leave": cmd.leave_channel,
            "/quit": cmd.disconnect,
            "/exit": cmd.exit_client
        }

    def parse_message(self, text: str) -> str:
        if not text.rstrip(" "):
            return ""
        if text.startswith("/"):
            try:
                args = text.split(" ")
                command_name = args[0]
                command_args = args[1:]
                if command_name not in self.commands:
                    print("Неизвестная команда")
                    return ""
                result = self.commands[command_name](*command_args)
            except TypeError:
                print(f"Неверное количество аргументов для команды: {command_name}")
                return ""
            else:
                return result

        return f"PRIVMSG {self.client.current_channel} :{text}"


class Response:
    COMMAND_REPR = {
        "JOIN": "joined",
        "PART": "left",
        "NICK": "is now known as",
        "MODE": "sets mode:"
    }

    def __init__(self, raw_response: bytes, code_page: str):
        self.decoded_data = raw_response.decode(code_page)

    def from_bytes(self) -> str:
        lines = self.decoded_data.split("\r\n")
        result = []
        for current_line in lines:
            for expr in [MESSAGE_EXPR, NOTIFICATION_EXPR, SERVER_MSG_EXPR]:
                match = expr.search(current_line)  # TODO: сделать норм название переменной
                if match:
                    current_line = self.parse_match_obj(match, expr.pattern)
                    break
            result.append(current_line)
        return "\r\n".join(result)

    def parse_match_obj(self, expr, pattern: str) -> str:
        groups = expr.groupdict()
        if pattern == NOTIFICATION_EXPR.pattern:
            return f"<{groups['nick']}> {self.COMMAND_REPR[groups['command']]} {groups['target']}"

        # if groups["target"] == self.nickname and groups["command"] == "PRIVMSG": TODO: Придумать как реализовать PM
        #     return f"PM from <{groups['sender']}>: {groups['text']}"

        if groups["command"] == "PRIVMSG":
            return f"[{groups['target']}] <{groups['sender']}>: {groups['text']}"

        return f"[{groups['sender']}] >> {groups['text']}"

    def __str__(self):
        return self.from_bytes()
