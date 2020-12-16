import abc
from irc.messages import ServerMessage


class BaseView(abc.ABC):
    @abc.abstractmethod
    def display_chat_text(self, text: str):  # TODO: Rename
        pass

    @abc.abstractmethod
    def display_server_message(self, message: ServerMessage):
        pass

    @abc.abstractmethod
    def display_channel(self, channel: str):
        pass
