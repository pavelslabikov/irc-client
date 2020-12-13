import socket
import re
import irc.const as const
import abc
import logging

logger = logging.getLogger(__name__)


class ClientCommand(abc.ABC):
    usage: str

    def __init__(self, client, *args):
        self._client = client
        self._args = args
        self.output = None

    def validate_args(self) -> bool:
        if len(self._args) + 1 != len(self.usage.split(" ")):
            self.output = f"Неверное количество аргументов для команды!\nИспользуйте: {self.usage}"
            return False
        return True

    @abc.abstractmethod
    def execute(self, *args):
        pass

    def __call__(self) -> str:
        if self.validate_args():
            result = self.execute(*self._args)
            return result + "\r\n" if result else ""
        return ""


class PartCommand(ClientCommand):
    usage = "/leave"

    def execute(self) -> str:
        ch_name = self._client.current_channel
        self._client.current_channel = None
        self._client.joined_channels.remove(ch_name)
        return f"PART {ch_name}"

    def validate_args(self) -> bool:
        if not super().validate_args():
            return False

        if not self._client.is_connected:
            self.output = "Прежде чем вводить данную команду, подключитесь к серверу!"
            return False

        ch_name = self._client.current_channel
        if ch_name not in self._client.joined_channels:
            self.output = f"Вы не присоединены ни к одному каналу!"
            return False
        return True


class ListCommand(ClientCommand):
    usage = "/list"

    def execute(self) -> str:
        return "LIST"


class NamesCommand(ClientCommand):
    usage = "/names"

    def execute(self) -> str:
        return f"NAMES {self._client.current_channel}"


class PrivateMessageCommand(ClientCommand):
    usage = "/pm TARGET TEXT"

    def validate_args(self) -> bool:
        if len(self._args) < 2:
            self.output = f"Неверное количество аргументов для команды!\nИспользуйте: {self.usage}"
            return False
        return True

    def execute(self, target: str, *message) -> str:
        return f"PRIVMSG {target} :{' '.join(message)}"


class JoinCommand(ClientCommand):
    usage = "/join CHANNEL [PASSWORD]"

    def execute(self, ch_name: str, password="") -> str:
        ch_name = ch_name.lower()
        self._client.current_channel = ch_name
        self._client.joined_channels.add(ch_name)
        return f"JOIN {ch_name} {password}"

    def validate_args(self) -> bool:
        if len(self._args) != 1 and len(self._args) != 2:
            self.output = f"Неверное количество аргументов для команды!\nИспользуйте: {self.usage}"
            return False

        if not self._client.is_connected:
            self.output = "Прежде чем вводить данную команду, подключитесь к серверу!"
            return False

        ch_name = self._args[0].lower()
        if ch_name in self._client.joined_channels:
            self.output = "Вы уже присоединились к данному каналу!"
            return False
        return True


class NickCommand(ClientCommand):
    NICK_EXPR = re.compile(r"^[a-zA-Zа-я-А-Я][\w]+")
    usage = "/nick NICKNAME"

    def execute(self, new_nickname: str) -> str:
        self._client.prev_nick = self._client.nickname
        self._client.nickname = new_nickname
        return f"NICK {new_nickname}"

    def validate_args(self) -> bool:
        if not super().validate_args():
            return False

        new_nickname = self._args[0]
        if not self.NICK_EXPR.search(new_nickname):
            self.output = "Недопустимый никнейм!"
            return False
        return True


class DisconnectCommand(ClientCommand):
    usage = "/quit"

    def execute(self) -> None:
        self._client.hostname = None
        self._client.is_connected = False
        self._client.joined_channels = set()
        self._client.current_channel = None
        self._client.sock.shutdown(socket.SHUT_WR)
        self.output = f"Отключение от сервера..."

    def validate_args(self) -> bool:
        if not super().validate_args():
            return False

        if not self._client.is_connected:
            self.output = "Прежде чем вводить данную команду, подключитесь к серверу!"
            return False
        return True


class SwitchCommand(ClientCommand):
    usage = "/switch CHANNEL"

    def execute(self, ch_name: str) -> None:
        ch_name = ch_name.lower()
        if ch_name in self._client.joined_channels and ch_name != self._client.current_channel:
            self.output = f"Переключение текущего канала на {ch_name}..."
            self._client.current_channel = ch_name

    def validate_args(self) -> bool:
        if not super().validate_args():
            return False

        if not self._client.is_connected:
            self.output = "Прежде чем вводить данную команду, подключитесь к серверу!"
            return False

        ch_name = self._args[0].lower()
        if ch_name not in self._client.joined_channels:
            self.output = f"Вы не присоединены к каналу {ch_name}!"
            return False

        if ch_name == self._client.current_channel:
            self.output = f"Вашим активным каналом уже является {ch_name}!"
            return False
        return True


class HelpCommand(ClientCommand):
    usage = "/help"

    def execute(self) -> None:
        self.output = const.HELP_MESSAGE


class ConnectCommand(ClientCommand):
    usage = "/server HOSTNAME [PORT]"

    def validate_args(self) -> bool:
        if len(self._args) != 1 and len(self._args) != 2:
            self.output = f"Неверное количество аргументов для команды!\nИспользуйте: {self.usage}"
            return False

        if self._client.is_connected:
            self.output = "Вы уже подключены к серверу!"
            return False
        return True

    def execute(self, hostname: str, port=6667) -> str:
        self._client.sock = socket.socket()
        self._client.sock.settimeout(10)
        try:
            logger.info(f"Trying to connect to {hostname} with port {port}...")
            self._client.sock.connect((hostname, port))
        except socket.gaierror as e:
            logger.info(f"Failed to connect by reason - {str(e)}")
            self.output = f"Не удалось подключиться по заданному адресу: {hostname}"
            return ""

        logger.info("Successfully connected to server.")
        self._client.sock.settimeout(None)
        self._client.hostname = hostname
        self._client.is_connected = True
        return f"NICK {self._client.nickname}\r\nUSER 1 1 1 1"


class CodePageCommand(ClientCommand):
    usage = "/chcp ENCODING"

    def validate_args(self) -> bool:
        if not super().validate_args():
            return False

        code_page = self._args[0].lower()
        if code_page not in const.CODE_PAGES:
            self.output = f"Допустимые кодировки: {const.CODE_PAGES}"
            return False
        return True

    def execute(self, code_page: str) -> None:
        self._client.code_page = code_page
        self.output = f"Текущая кодировка изменена на {code_page}"


class AddToFavCommand(ClientCommand):
    usage = "/add"

    def validate_args(self) -> bool:
        if not super().validate_args():
            return False

        if not self._client.is_connected:
            self.output = "Прежде чем вводить данную команду, подключитесь к серверу!"
            return False

        return True

    def execute(self) -> None:
        self._client.favourites.add(self._client.hostname)
        self.output = f"Сервер {self._client.hostname} добавлен в список избранных"


class ShowFavCommand(ClientCommand):
    usage = "/fav"

    def execute(self) -> None:
        servers = []
        for server in self._client.favourites:
            servers.append(server)
        self.output = "Список серверов в избранном:\n" + "\n".join(servers)


class ExitCommand(ClientCommand):
    usage = "/exit"

    def execute(self) -> None:
        logger.info("Exiting application")
        self._client.is_working = False
        if self._client.is_connected:
            self._client.is_connected = False
            self._client.sock.shutdown(socket.SHUT_WR)


class UnknownCommand(ClientCommand):
    def validate_args(self) -> bool:
        return True

    def execute(self, *args) -> None:
        pass
