from irc.view import BaseView
from irc.server_messages import ServerMessage


class CliView(BaseView):
    def display_server_message(self, message: ServerMessage):
        if message:
            print(message)

    def display_text(self, text: str):
        if text:
            print(text)
