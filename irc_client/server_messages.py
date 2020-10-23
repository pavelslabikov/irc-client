import abc
import re


class ServerMessage(abc.ABC):
    expr = re.compile("")

    def __init__(self, client, raw_message: str):
        self._client = client
        self.raw_message = raw_message

    @abc.abstractmethod
    def get_parsed_message(self, **kwargs) -> str:
        pass

    def __str__(self):
        match = self.expr.search(self.raw_message)
        if match:
            return self.get_parsed_message(**match.groupdict())
        return self.raw_message


class JoinMessage(ServerMessage):
    expr = re.compile(r":(?P<nick>[^\s!]+)!?\S+ JOIN :?(?P<channel>\S+)")

    def get_parsed_message(self, nick, channel) -> str:
        return f"{nick} присоединился к {channel}"


class PartMessage(ServerMessage):
    expr = re.compile(r":(?P<nick>[^\s!]+)!?\S+ PART :?(?P<channel>\S+)")

    def get_parsed_message(self, nick, channel) -> str:
        return f"{nick} покинул {channel}"


class NoticeMessage(ServerMessage):
    expr = re.compile(r":(?P<sender>[^\s!]+)(!.*)? NOTICE .+ :(?P<text>.+)")

    def get_parsed_message(self, sender, text) -> str:
        return f"[{sender}] >> {text}"


class PrivateMessage(ServerMessage):
    expr = re.compile(r":(?P<sender>[^\s!]+)(!.*)? PRIVMSG (?P<target>.+) :(?P<text>.+)")

    def get_parsed_message(self, sender, target, text) -> str:
        return f"[{target}] <{sender}>: {text}"


class ModeMessage(ServerMessage):
    expr = re.compile(r":(?P<nick>\S+) MODE (?P<target>.+) :?(?P<mode>\S+)")

    def get_parsed_message(self, nick, target, mode) -> str:
        if target == nick:
            return f"{nick} сменил свой флаг на {mode}"

        return f"{nick} установил для {target} флаг {mode}"


class ServiceMessage(ServerMessage):
    expr = re.compile(r":(?P<sender>[^\s!]+)(!.*)? (?P<code>\d{3}) \S+ :?(?P<text>.+)")
    CHAN_ERRORS = {442, 470, 471, 473, 474, 475, 477, 478}
    NICK_ERROR = 433

    def get_parsed_message(self, sender: str, text: str, code: str) -> str:
        response_code = int(code)
        if response_code in self.CHAN_ERRORS:
            curr_channel = self._client.current_channel
            if curr_channel in self._client.joined_channels:
                self._client.joined_channels.remove(curr_channel)
            self._client.current_channel = None

        if response_code == self.NICK_ERROR:
            self._client.nickname = self._client.prev_nick
        return f"[{sender}] >> {text}"


class NickMessage(ServerMessage):
    expr = re.compile(r":(?P<nick>[^\s!]+)!?\S+ NICK.* :?(?P<new_nick>\S+)")

    def get_parsed_message(self, nick, new_nick) -> str:
        return f"{nick} сменил ник на {new_nick}"
