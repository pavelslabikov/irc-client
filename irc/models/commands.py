import socket
import re
import abc
import logging

from irc import const


logger = logging.getLogger(__name__)

ERR_ARGS_AMOUNT = "Неверное кол-во аргументов для команды\nИспользуйте: "
ERR_NOT_CONNECTED = "Сначала подключитесь к серверу"


class ClientCommand(abc.ABC):
    usage: str

    def __init__(self, client, *args):
        self._client = client
        self._args = args
        self.output = None

    def validate_args(self) -> bool:
        if len(self._args) + 1 != len(self.usage.split(" ")):
            self.output = ERR_ARGS_AMOUNT + self.usage
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
            self.output = ERR_NOT_CONNECTED
            return False

        ch_name = self._client.current_channel
        if ch_name not in self._client.joined_channels:
            self.output = "Вы не присоединены ни к одному каналу!"
            return False
        return True


class ListCommand(ClientCommand):
    usage = "/list"

    def execute(self) -> str:
        return "LIST"


class NamesCommand(ClientCommand):
    usage = "/names"

    def validate_args(self) -> bool:
        if not super().validate_args():
            return False

        if not self._client.current_channel:
            self.output = "Не выбран активный канал! Используйте /switch"
            return False

    def execute(self) -> str:
        return f"NAMES {self._client.current_channel}"


class WhisperCommand(ClientCommand):
    usage = "/pm TARGET TEXT"

    def validate_args(self) -> bool:
        if len(self._args) < 2:
            self.output = ERR_ARGS_AMOUNT + self.usage
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
            self.output = ERR_ARGS_AMOUNT + self.usage
            return False

        if not self._client.is_connected:
            self.output = ERR_NOT_CONNECTED
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


class QuitCommand(ClientCommand):
    usage = "/quit"

    def execute(self) -> None:
        self._client.hostname = None
        self._client.is_connected = False
        self._client.joined_channels = set()
        self._client.current_channel = None
        self._client.sock.shutdown(socket.SHUT_WR)
        self.output = "Отключение от сервера..."

    def validate_args(self) -> bool:
        if not super().validate_args():
            return False

        if not self._client.is_connected:
            self.output = ERR_NOT_CONNECTED
            return False
        return True


class SwitchCommand(ClientCommand):
    usage = "/switch [CHANNEL]"

    def execute(self, ch_name: str) -> None:
        ch_name = ch_name.lower()
        self.output = f"Переключение текущего канала на {ch_name}..."
        self._client.current_channel = ch_name

    def validate_args(self) -> bool:
        if len(self._args) != 0 and len(self._args) != 1:
            self.output = ERR_ARGS_AMOUNT + self.usage
            return False
        if len(self._args) == 0:
            self.output = f"Активный канал: {self._client.current_channel}\n"
            channel_list = ' '.join(self._client.joined_channels)
            self.output += f"Присоединённые каналы: {channel_list}"
            return False
        if not self._client.is_connected:
            self.output = ERR_NOT_CONNECTED
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
            self.output = ERR_ARGS_AMOUNT + self.usage
            return False

        if self._client.is_connected:
            self.output = "Вы уже подключены к серверу!"
            return False
        return True

    def execute(self, hostname: str, port=6667) -> str:
        self._client.sock = socket.socket()
        self._client.sock.settimeout(10)
        try:
            logger.info(f"Trying to connect to {hostname}")
            self._client.sock.connect((hostname, port))
        except socket.gaierror as e:
            logger.info(f"Failed to connect by reason - {str(e)}")
            self.output = f"Не удалось подключиться по адресу: {hostname}"
            return ""
        except OSError:
            self.output = f"Не удалось подключиться по адресу: {hostname}"
            return ""

        logger.info("Successfully connected to server.")
        self._client.sock.settimeout(None)
        self._client.hostname = hostname.lower()
        self._client.is_connected = True
        self.set_joined_channels(self._client.favourites.get(hostname))
        return f"NICK {self._client.nickname}\r\nUSER 1 1 1 1"

    def set_joined_channels(self, channels_to_join: str):
        if channels_to_join:
            for channel in channels_to_join.split(","):
                self._client.joined_channels.add(channel)


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


class AddFavCommand(ClientCommand):
    usage = "/add"

    def validate_args(self) -> bool:
        if not super().validate_args():
            return False

        if not self._client.is_connected:
            self.output = ERR_NOT_CONNECTED
            return False

        if self._client.hostname in self._client.favourites:
            self.output = "Сервер уже в списке избранных"
            return False

        return True

    def execute(self) -> None:
        self._client.favourites[self._client.hostname] = ""
        self.output = f"Сервер {self._client.hostname} добавлен в избранное"


class ShowFavCommand(ClientCommand):
    usage = "/fav"

    def execute(self) -> None:
        servers = []
        for server in self._client.favourites.keys():
            servers.append(server)
        self.output = "Список серверов в избранном:\n" + "\n".join(servers)


class ExitCommand(ClientCommand):
    usage = "/exit"

    def execute(self) -> None:
        logger.info("Closing application")
        self._client.exit_client()


class UnknownCommand(ClientCommand):
    def validate_args(self) -> bool:
        return True

    def execute(self, *args) -> None:
        pass
