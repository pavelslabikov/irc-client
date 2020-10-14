import socket
import threading
import logging
import irc_client.const as const
import irc_client.commands as cmd
import irc_client.server_messages as msg
from configparser import ConfigParser

logger = logging.getLogger(__name__)


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
        handler = CommandHandler(self)
        while self.is_working:
            message = handler.parse_input(input(self.cmd_prompt))
            if self.is_connected:
                self.sock.sendall(message)

    def wait_for_response(self) -> None:
        parser = ResponseParser(self)
        while self.is_working:
            while self.is_connected:
                data = self.sock.recv(const.BUFFER_SIZE)
                print(parser.parse_response(data))

    def refresh_config(self) -> None:
        logger.debug(f"Trying to refresh config by path: {const.CONFIG_PATH}")
        with open(const.CONFIG_PATH, "w") as file:
            self.config.write(file)


class CommandHandler:
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
            "/switch": cmd.SwitchCommand,
            "/knock": cmd.Info
        }

    def get_command(self, line: str) -> cmd.ClientCommand:
        args = line.split(" ")
        command_name = args[0]
        cmd_args = args[1:]
        if command_name in self.commands:
            return self.commands[command_name](self.client, *cmd_args)
        logger.debug(f"Cannot parse command: {command_name}")
        return cmd.UnknownCommand(self.client, *cmd_args)

    def parse_input(self, input_text: str) -> bytes:
        text_to_send = bytearray()
        if input_text.startswith("/"):
            command = self.get_command(input_text)
            text_to_send += command().encode(self.client.code_page) + b"\r\n"
            print(command.output)

        elif self.client.current_channel and input_text.rstrip(" "):
            pm_command = self.get_command(f"/pm {self.client.current_channel} {input_text}")
            text_to_send += pm_command().encode(self.client.code_page) + b"\r\n"
        return text_to_send


class ResponseParser:
    def __init__(self, client: Client):
        self.client = client
        self.messages = {
            "JOIN": msg.JoinMessage,
            "PART": msg.PartMessage,
            "NICK": msg.NickMessage,
            "MODE": msg.ChangeModeMessage,
            "PRIVMSG": msg.PrivateMessage,
            "NOTICE": msg.NoticeMessage
        }

    def get_messages(self, decoded_data: str):
        for line in decoded_data.split("\r\n"):
            words = line.split(" ")
            if len(words) < 2:
                continue
            command_name = words[1].upper()
            if command_name in self.messages:
                yield self.messages[command_name](line)
            elif command_name.isdigit():
                yield msg.ServiceMessage(line)
            else:
                logger.debug(f"Received unresolved message: {line}")
                yield msg.UnresolvedMessage(line)

    def parse_response(self, data: bytes) -> str:
        decoded_data = data.decode(self.client.code_page)
        result = [str(message) for message in self.get_messages(decoded_data)]
        return "\n".join(result)
