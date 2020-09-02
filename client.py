import socket
import threading
import re

CHUNK_SIZE = 1024

MESSAGE_EXPR = re.compile(r":(?P<sender>[^\s!]+)(!.*)? (?P<command>PRIVMSG|NOTICE|\d{3}) (?P<target>.+) :(?P<text>.+)")
NOTIFICATION_EXPR = re.compile(r":(?P<nick>[^\s!]+)!?\S+ (?P<command>JOIN|PART|NICK|MODE).* :?(?P<target>\S+)")

COMMAND_REPR = {
    "JOIN": "joined",
    "PART": "left",
    "NICK": "is now known as",
    "MODE": "sets mode:"
}


class Client:
    def __init__(self):
        self.sock = socket.socket()
        self.nickname = "default"
        self.joined_channels = set()
        self.current_channel = ""
        self.is_connected = False
        self.is_working = True
        self.parser = InputParser(self)

    def start_client(self):
        input_thread = threading.Thread(target=self.wait_for_input)
        input_thread.daemon = True
        input_thread.start()
        while self.is_working:
            while self.is_connected:
                data = self.sock.recv(CHUNK_SIZE)
                print(self.parse_message(data.decode("cp1251")))
        input_thread.join()

    def wait_for_input(self):
        while self.is_working:
            message = self.parser.parse_message(input()) + "\r\n"
            if self.is_connected:
                self.sock.sendall(bytes(message, "cp1251"))

    def parse_message(self, raw_message: str) -> str:
        result = []
        for current in raw_message.split("\r\n"):
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
            return f"<{groups['nick']}> {COMMAND_REPR[groups['command']]} {groups['target']}"

        if groups["target"] == self.nickname and groups["command"] == "PRIVMSG":
            return f"PM from <{groups['sender']}>: {groups['text']}"

        if groups["command"] == "PRIVMSG":
            return f"[{groups['target']}] <{groups['sender']}>: {groups['text']}"

        return f"[{groups['sender']}] >> {groups['text']}"


class InputParser:
    def __init__(self, client: Client):
        self.client = client
        cmd = ClientCommand(client)
        self.commands = {
            "/ns": cmd.send_to_nick_service,
            "/nick": cmd.change_nick,
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


class ClientCommand:
    def __init__(self, client: Client):
        self.client = client

    def change_nick(self, new_nickname: str) -> str:
        self.client.nickname = new_nickname
        return f"NICK {new_nickname}"

    def send_to_nick_service(self, *args) -> str:
        return f"PRIVMSG nickserv :{' '.join(args)}"

    def join_channel(self, ch_name: str, password="") -> str:
        if ch_name.lower() in self.client.joined_channels:
            print("Вы уже присоединились к данному каналу!")
            return ""
        self.client.current_channel = ch_name
        self.client.joined_channels.add(ch_name.lower())
        return f"JOIN {ch_name} {password}"

    def disconnect(self) -> str:
        self.client.is_connected = False
        self.client.joined_channels = set()
        self.client.current_channel = ""
        self.client.sock.shutdown(socket.SHUT_WR)
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
        print(f"Сейчас вы пишете в канале: {self.client.current_channel}")
        if ch_name.lower() in self.client.joined_channels:
            print(f"Переключение текущего канала на {ch_name}...")
            self.client.current_channel = ch_name
        return ""

    def leave_channel(self) -> str:
        current = self.client.current_channel
        if current in self.client.joined_channels:
            self.client.current_channel = ""
            self.client.joined_channels.remove(current)
        return f"PART {current}"

    def exit_client(self):
        self.client.is_working = False
        if self.client.is_connected:
            self.client.is_connected = False
            self.client.sock.shutdown(socket.SHUT_WR)
        exit()


c = Client()
c.start_client()
