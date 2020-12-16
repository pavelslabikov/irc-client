from irc.view import BaseView
from irc.models.messages import ServerMessage


class CliView(BaseView):
    def display_server_message(self, message: ServerMessage):
        if message:
            print(message)

    def display_chat_text(self, text: str):
        if text:
            print(text)

    def display_channel(self, channel: str):
        pass
