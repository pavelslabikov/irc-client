import socket
import re

NICK_EXPR = re.compile(r"^[a-zA-Zа-я-А-Я][\w]+")
CODE_PAGES = {"cp1251", "koi8_r", "cp866", "mac_cyrillic", "iso8859_5"}


class ClientCommand:
    def __init__(self, client):
        self.client = client

    def change_nick(self, new_nickname: str) -> str:
        if not NICK_EXPR.search(new_nickname):
            print("Недопустимый никнейм!")
            return ""
        self.client.config["Settings"]["nickname"] = new_nickname
        self.client.nickname = new_nickname
        return f"NICK {new_nickname}"

    def send_to_nick_service(self, *args) -> str:
        return f"PRIVMSG nickserv :{' '.join(args)}"

    def send_to_chan_service(self, *args) -> str:
        return f"PRIVMSG chanserv :{' '.join(args)}"

    def send_to_bot_service(self, *args) -> str:
        return f"PRIVMSG botserv :{' '.join(args)}"

    def join_channel(self, ch_name: str, password="") -> str:
        if not self.client.is_connected:
            return ""
        ch_name = ch_name.lower()
        if ch_name in self.client.joined_channels:
            print("Вы уже присоединились к данному каналу!")
            return ""
        self.client.current_channel = ch_name
        self.client.joined_channels.add(ch_name)
        return f"JOIN {ch_name} {password}"

    def disconnect(self) -> str:
        if not self.client.is_connected:
            return ""
        self.client.host_name = ""
        self.client.is_connected = False
        self.client.joined_channels = set()
        self.client.current_channel = ""
        self.client.sock.shutdown(socket.SHUT_WR)
        return ""

    def change_code_page(self, code_page: str) -> str:
        if not code_page.lower() in CODE_PAGES:
            print(f"Допустимые кодировки: {CODE_PAGES}")
            return ""
        print(f"Текущая кодировка изменена на {code_page}")
        self.client.code_page = code_page
        self.client.config.set("Settings", "CodePage", code_page)
        return ""

    def add_to_favourites(self) -> str:
        if not self.client.is_connected:
            return ""
        host = self.client.hostname
        if self.client.config.has_option("Servers", host):
            print("Сервер уже находится в списке избранных")
            return ""
        print(f"Сервер {host} добавлен в список избранных")
        self.client.config.set("Servers", host)
        return ""

    def show_favourites(self) -> str:
        print("Список серверов в избранном:")
        for server, value in self.client.config.items("Servers"):
            print(server)
        return ""

    def connect(self, server: str, port=6667) -> str:
        if self.client.is_connected:
            return ""
        print(f"Подключение к {server}...")
        self.client.sock = socket.socket()
        self.client.sock.settimeout(10)
        try:
            self.client.sock.connect((server, port))
        except socket.gaierror:
            print(f"Не удалось подключиться по заданному адресу: {server}")
            return ""
        self.client.sock.settimeout(None)
        self.client.host_name = server
        self.client.is_connected = True
        return f"NICK {self.client.nickname}\r\nUSER 1 1 1 1"

    def show_names(self) -> str:
        return f"NAMES {self.client.current_channel}"

    def switch_channel(self, ch_name) -> str:
        if not self.client.is_connected:
            return ""
        ch_name = ch_name.lower()
        if ch_name in self.client.joined_channels and ch_name != self.client.current_channel:
            print(f"Переключение текущего канала на {ch_name}...")
            self.client.current_channel = ch_name
        return ""

    def show_channels(self) -> str:
        return "LIST"

    def leave_channel(self) -> str:
        if not self.client.is_connected:
            return ""
        current = self.client.current_channel.lower()
        if current in self.client.joined_channels:
            self.client.current_channel = ""
            self.client.joined_channels.remove(current)
        return f"PART {current}"

    def exit_client(self) -> None:
        self.client.refresh_config()
        self.client.is_working = False
        if self.client.is_connected:
            self.client.is_connected = False
            self.client.sock.shutdown(socket.SHUT_WR)
        exit()