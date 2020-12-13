import abc
from irc.server_messages import ServerMessage


class BaseView(abc.ABC):
    @abc.abstractmethod
    def display_text(self, text: str):  # TODO: Rename
        pass

    @abc.abstractmethod
    def display_server_message(self, message: ServerMessage):
        pass


