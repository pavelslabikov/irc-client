import socket
import threading
import logging
import irc_client.const as const
import irc_client.commands as com
import irc_client.server_messages as msg

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, nickname: str, code_page: str, favourites: set):
        self.sock = socket.socket()
        self.favourites = favourites
        self.nickname = nickname
        self.prev_nick = nickname
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
            command = handler.get_command(input(self.cmd_prompt))
            execution_result = command().encode(self.code_page)
            if self.is_connected:
                self.sock.sendall(execution_result)
            if command.output:
                print(command.output)

    def wait_for_response(self) -> None:
        handler = MessageHandler(self)
        while self.is_working:
            while self.is_connected:
                data = self.sock.recv(const.BUFFER_SIZE)
                print(handler.parse_response(data))


class CommandHandler:
    def __init__(self, client: Client):
        self.client = client
        self.commands = {
            "/chcp": com.CodePageCommand,
            "/nick": com.NickCommand,
            "/help": com.HelpCommand,
            "/fav": com.ShowFavCommand,
            "/server": com.ConnectCommand,
            "/exit": com.ExitCommand,
            "/pm": com.PrivateMessageCommand,
            "/add": com.AddToFavCommand,
            "/join": com.JoinCommand,
            "/list": com.ListCommand,
            "/names": com.NamesCommand,
            "/leave": com.PartCommand,
            "/quit": com.DisconnectCommand,
            "/switch": com.SwitchCommand,
        }

    def get_command(self, input_text: str) -> com.ClientCommand:
        if input_text.startswith("/"):
            command_parts = input_text.split(" ")
            command_name = command_parts[0]
            command_args = command_parts[1:]
            if command_name in self.commands:
                return self.commands[command_name](self.client, *command_args)

        elif self.client.current_channel and input_text.rstrip(" "):
            return com.PrivateMessageCommand(self.client, self.client.current_channel, *input_text.split(" "))

        logger.debug(f"Cannot parse command: {input_text}")
        return com.UnknownCommand(self.client)


class MessageHandler:
    def __init__(self, client: Client):
        self.client = client
        self.messages = {
            "JOIN": msg.JoinMessage,
            "PART": msg.PartMessage,
            "NICK": msg.NickMessage,
            "MODE": msg.ModeMessage,
            "PRIVMSG": msg.PrivateMessage,
            "NOTICE": msg.NoticeMessage
        }

    def get_messages(self, decoded_data: str):
        for line in decoded_data.split("\r\n"):
            words = line.split(" ")
            if len(words) < 2:
                logger.debug(f"Received too short message: {line}")
                continue
            command_name = words[1].upper()
            if command_name in self.messages:
                yield self.messages[command_name](self.client, line)
            elif command_name.isdigit():
                yield msg.ServiceMessage(self.client, line)
            else:
                logger.debug(f"Received unresolved message: {line}")
                continue
        return ""

    def parse_response(self, data: bytes) -> str:
        decoded_data = data.decode(self.client.code_page)
        result = [str(message) for message in self.get_messages(decoded_data)]
        return "\n".join(result)
