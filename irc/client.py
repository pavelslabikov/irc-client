import socket
import time
import logging

from irc import const
from irc.handlers import CommandHandler, MessageHandler
from irc.view import BaseView

logger = logging.getLogger(__name__)


class Client:
    def __init__(
        self, nickname: str, encoding: str, favourites: set, view: BaseView
    ):
        self.sock = socket.socket()
        self.favourites = favourites
        self.nickname = nickname
        self.prev_nick = nickname
        self.code_page = encoding
        self.hostname = None
        self.view = view
        self.joined_channels = set()
        self.current_channel = None
        self.is_connected = False
        self.is_working = True
        self.command_handler = CommandHandler(self)

    def process_user_input(self, text: str) -> None:
        command = self.command_handler.get_command(text)
        execution_result = command().encode(self.code_page)
        if self.is_connected:
            self.sock.sendall(execution_result)
        self.view.display_chat_text(command.output)

    def wait_for_response(self) -> None:
        handler = MessageHandler(self)
        while self.is_working:
            time.sleep(0.1)
            while self.is_connected:
                raw_data = self.sock.recv(const.BUFFER_SIZE)
                decoded_data = raw_data.decode(self.code_page)
                for msg in handler.get_messages(decoded_data):
                    self.view.display_server_message(msg)

    def exit_client(self) -> None:
        self.is_working = False
        if self.is_connected:
            self.is_connected = False
            self.sock.shutdown(socket.SHUT_WR)
