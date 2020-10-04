import socket
import threading
import re
import app.const as const
import app.commands as cmd
from configparser import ConfigParser

MESSAGE_EXPR = re.compile(r":(?P<sender>[^\s!]+)(!.*)? (?P<command>PRIVMSG|NOTICE|\d{3}) (?P<target>.+) :(?P<text>.+)")
NOTIFICATION_EXPR = re.compile(r":(?P<nick>[^\s!]+)!?\S+ (?P<command>JOIN|PART|NICK|MODE).* :?(?P<target>\S+)")
SERVER_MSG_EXPR = re.compile(r":(?P<sender>\S+) (?P<command>\d{3}) \S+ (?P<text>.+) :")


class Client:
    def __init__(self, config: ConfigParser, nickname: str, code_page: str):
        self.sock = socket.socket()
        self.config = config
        self.nickname = nickname
        self.code_page = code_page
        self.hostname = None
        self.joined_channels = set()
        self.current_channel = None
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
                self.sock.sendall(message.encode(self.code_page))

    def wait_for_response(self) -> None:
        while self.is_working:
            while self.is_connected:
                data = self.sock.recv(const.BUFFER_SIZE)
                print(Response(data, self.code_page))

    def refresh_config(self) -> None:
        with open(const.CONFIG_PATH, "w") as file:
            self.config.write(file)


class InputParser:
    def __init__(self, client: Client):
        self.client = client
        self.commands = {
            "/chcp": cmd.ChangeCodePageCommand,
            "/nick": cmd.ChangeNickCommand,
            "/help": cmd.HelpCommand,
            "/fav": cmd.ShowFavCommand,
            "/server": cmd.ConnectCommand,
            "/exit": cmd.ExitCommand,
            "/pm": cmd.PrivateMessageCommand,
            "/add": cmd.AddToFavCommand,
            "/join": cmd.JoinCommand,
            "/list": cmd.ShowChannelsCommand,
            "/names": cmd.ShowNamesCommand,
            "/leave": cmd.LeaveCommand,
            "/quit": cmd.DisconnectCommand,
            "/switch": cmd.SwitchCommand
        }

    def parse_message(self, text: str) -> str:
        if text.startswith("/"):
            args = text.split(" ")
            result = None
            cmd_name = args[0]
            cmd_args = args[1:]
            if cmd_name in self.commands:
                command = self.commands[cmd_name](self.client, *cmd_args)
                result = command()
                print(command.output)
            else:
                print("Неизвестная команда")
            if result:
                return result
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
