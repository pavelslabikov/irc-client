from irc.gui.window import ClientWindow
from irc.view import BaseView
from irc.models.messages import ServerMessage


class GuiView(BaseView):
    def __init__(self, window: ClientWindow):
        self.window = window

    def display_chat_text(self, text: str):
        if text:
            self.window.print_signal.emit(text)

    def display_server_message(self, message: ServerMessage):
        if message:
            self.window.print_signal.emit(str(message))

    def display_channel(self, channel: str):
        if channel:
            self.window.print_channel_signal.emit(channel)
