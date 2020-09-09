import socket
import threading
import re
from configparser import ConfigParser

CHUNK_SIZE = 1024

MESSAGE_EXPR = re.compile(r":(?P<sender>[^\s!]+)(!.*)? (?P<command>PRIVMSG|NOTICE|\d{3}) (?P<target>.+) :(?P<text>.+)")
NOTIFICATION_EXPR = re.compile(r":(?P<nick>[^\s!]+)!?\S+ (?P<command>JOIN|PART|NICK|MODE).* :?(?P<target>\S+)")

CODE_PAGES = {"cp1251", "koi8", "translit", "dos", "mac", "iso"}


class Client:
    def __init__(self, config: ConfigParser):
        self.sock = socket.socket()
        self.config = config
        self.nickname = config.get("Settings", "Nickname")
        self.code_page = config.get("Settings", "CodePage")
        self.joined_channels = set()
        self.current_channel = ""
        self.is_connected = False
        self.is_working = True
        self.parser = InputParser(self)

    @property
    def cmd_prompt(self):
        if not self.current_channel:
            return f"<{self.nickname}>: "
        return f"[{self.current_channel}] <{self.nickname}>: "

    def start_client(self) -> None:
        input_thread = threading.Thread(target=self.wait_for_input)
        input_thread.daemon = True
        input_thread.start()
        self.wait_for_response()
        input_thread.join()

    def wait_for_input(self) -> None:
        while self.is_working:
            message = self.parser.parse_message(input(self.cmd_prompt)) + "\r\n"
            if self.is_connected:
                self.sock.sendall(bytes(message, "cp1251"))

    def wait_for_response(self) -> None:
        while self.is_working:
            while self.is_connected:
                data = self.sock.recv(CHUNK_SIZE)
                print(str(Response(data, self.code_page)))


class InputParser:
    def __init__(self, client: Client):
        self.client = client
        cmd = ClientCommand(client)
        self.commands = {
            "/bs": cmd.send_to_bot_service,
            "/cs": cmd.send_to_chan_service,
            "/ns": cmd.send_to_nick_service,
            "/chcp": cmd.change_code_page,
            "/nick": cmd.change_nick,
            "/add": cmd.add_to_favourites,
            "/join": cmd.join_channel,
            "/server": cmd.connect,
            "/names": cmd.show_names,
            "/switch": cmd.switch_channel,
            "/leave": cmd.leave_channel,
            "/quit": cmd.disconnect,
            "/exit": cmd.exit_client
        }

    def parse_message(self, text: str) -> str:
        if text.startswith("/"):
            try:
                args = text.split(" ")
                command_name = args[0]
                command_args = args[1:]
                if command_name not in self.commands:
                    print("Неизвестная команда")
                    return ""
                result = self.commands[command_name](*command_args)
            except TypeError:
                print("Неверное количество аргументов для команды")
                return ""
            else:
                return result
        return f"PRIVMSG {self.client.current_channel} :{text}"


class Response:
    def __init__(self, raw_response: bytes, code_page: str):
        self.decoded_data = raw_response.decode(code_page)

    command_repr = {
        "JOIN": "joined",
        "PART": "left",
        "NICK": "is now known as",
        "MODE": "sets mode:"
    }

    def from_bytes(self) -> str:
        result = []
        for current in self.decoded_data.split("\r\n"):
            for expr in [MESSAGE_EXPR, NOTIFICATION_EXPR]:
                match = expr.search(current)  # TODO: сделать норм название переменной
                if match:
                    current = self.parse_match_obj(match, expr.pattern)
                    break
            result.append(current)
        return "\r\n".join(result)

    def parse_match_obj(self, expr, pattern: str) -> str:
        groups = expr.groupdict()
        if pattern == NOTIFICATION_EXPR.pattern:
            return f"<{groups['nick']}> {self.command_repr[groups['command']]} {groups['target']}"

        # if groups["target"] == self.nickname and groups["command"] == "PRIVMSG": TODO: Придумать как реализовать PM
        #     return f"PM from <{groups['sender']}>: {groups['text']}"

        if groups["command"] == "PRIVMSG":
            return f"[{groups['target']}] <{groups['sender']}>: {groups['text']}"

        return f"[{groups['sender']}] >> {groups['text']}"

    def __str__(self):
        return self.from_bytes()


class ClientCommand:
    def __init__(self, client: Client):
        self.client = client

    def change_nick(self, new_nickname: str) -> str:
        self.client.config.set("Settings", "Nickname", new_nickname)  # TODO: написать регулярку для никнейма
        self.client.nickname = new_nickname
        return f"NICK {new_nickname}"

    def send_to_nick_service(self, *args) -> str:
        return f"PRIVMSG nickserv :{' '.join(args)}"

    def send_to_chan_service(self, *args) -> str:
        return f"PRIVMSG chanserv :{' '.join(args)}"

    def send_to_bot_service(self, *args) -> str:
        return f"PRIVMSG botserv :{' '.join(args)}"

    def join_channel(self, ch_name: str, password="") -> str:
        ch_name = ch_name.lower()
        if ch_name in self.client.joined_channels:
            print("Вы уже присоединились к данному каналу!")
            return ""
        self.client.current_channel = ch_name
        self.client.joined_channels.add(ch_name)
        return f"JOIN {ch_name} {password}"

    def disconnect(self) -> str:
        if self.client.is_connected:
            self.client.is_connected = False
            self.client.joined_channels = set()
            self.client.current_channel = ""
            self.client.sock.shutdown(socket.SHUT_WR)
        return ""

    def change_code_page(self, code_page: str) -> str:
        if not code_page.lower() in CODE_PAGES:
            print("Недопустимая кодировка")
            return ""
        print(f"Текущая кодировка изменена на {code_page}")
        self.client.code_page = code_page
        self.client.config.set("Settings", "CodePage", code_page)
        return ""

    def add_to_favourites(self, host: str) -> str:
        if self.client.config.has_option("Servers", host):
            print("Сервер уже находится в списке избранных")
            return ""
        print(f"Сервер {host} добавлен в список избранных")
        self.client.config.set("Servers", host)
        return ""

    def connect(self, server: str, port=6667) -> str:
        print(f"Подключение к {server}...")
        self.client.sock = socket.socket()
        self.client.sock.connect((server, port))
        self.client.is_connected = True
        return f"NICK {self.client.nickname}\r\nUSER 1 1 1 1"

    def show_names(self) -> str:
        return f"NAMES {self.client.current_channel}"

    def switch_channel(self, ch_name="") -> str:
        ch_name = ch_name.lower()
        if ch_name in self.client.joined_channels and ch_name != self.client.current_channel:
            print(f"Переключение текущего канала на {ch_name}...")
            self.client.current_channel = ch_name
        return ""

    def leave_channel(self) -> str:
        current = self.client.current_channel
        if current in self.client.joined_channels:
            self.client.current_channel = ""
            self.client.joined_channels.remove(current.lower())
        return f"PART {current}"

    def refresh_config(self) -> None:
        with open("config.ini", "w") as file:
            self.client.config.write(file)

    def exit_client(self) -> None:
        self.refresh_config()
        self.client.is_working = False
        if self.client.is_connected:
            self.client.is_connected = False
            self.client.sock.shutdown(socket.SHUT_WR)
        exit()
