import abc
import re


class ServerMessage(abc.ABC):
    expr = re.compile("")

    def __init__(self, client, raw_message: str):
        self._client = client
        self.raw_message = raw_message

    @abc.abstractmethod
    def parse_from_str(self, match) -> str:
        pass

    def __str__(self):
        match = self.expr.search(self.raw_message)
        if match:
            return self.parse_from_str(match)
        return self.raw_message


class JoinMessage(ServerMessage):
    expr = re.compile(r":(?P<nick>[^\s!]+)!?\S+ JOIN :?(?P<channel>\S+)")

    def parse_from_str(self, match) -> str:
        nickname = match.groupdict()["nick"]
        channel = match.groupdict()["channel"]
        return f"{nickname} присоединился к {channel}"


class PartMessage(ServerMessage):
    expr = re.compile(r":(?P<nick>[^\s!]+)!?\S+ PART :?(?P<channel>\S+)")

    def parse_from_str(self, match) -> str:
        nickname = match.groupdict()["nick"]
        channel = match.groupdict()["channel"]
        return f"{nickname} покинул {channel}"


class NoticeMessage(ServerMessage):
    expr = re.compile(r":(?P<sender>[^\s!]+)(!.*)? NOTICE .+ :(?P<text>.+)")

    def parse_from_str(self, match) -> str:
        sender = match.groupdict()["sender"]
        text = match.groupdict()["text"]
        return f"[{sender}] >> {text}"


class PrivateMessage(ServerMessage):
    expr = re.compile(r":(?P<sender>[^\s!]+)(!.*)? PRIVMSG (?P<target>.+) :(?P<text>.+)")

    def parse_from_str(self, match) -> str:
        sender = match.groupdict()["sender"]
        target = match.groupdict()["target"]
        text = match.groupdict()["text"]
        return f"[{target}] <{sender}>: {text}"


class ChangeModeMessage(ServerMessage):
    expr = re.compile(r":(?P<nick>\S+) MODE (?P<target>.+) :?(?P<mode>\S+)")

    def parse_from_str(self, match) -> str:
        nickname = match.groupdict()["nick"]
        target = match.groupdict()["target"]
        new_mode = match.groupdict()["mode"]
        if target == nickname:
            return f"{nickname} сменил свой флаг на {new_mode}"

        return f"{nickname} установил для {target} флаг {new_mode}"


class ServiceMessage(ServerMessage):
    expr = re.compile(r":(?P<sender>[^\s!]+)(!.*)? (?P<code>\d{3}) \S+ :?(?P<text>.+)")
    CHAN_ERRORS = {442, 470, 471, 473, 474, 475, 477, 478}
    NICK_ERROR = 433

    def parse_from_str(self, match) -> str:
        sender = match.groupdict()["sender"]
        text = match.groupdict()["text"]
        response_code = int(match.groupdict()["code"])

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

    def parse_from_str(self, match) -> str:
        nickname = match.groupdict()["nick"]
        new_nickname = match.groupdict()["new_nick"]
        return f"{nickname} сменил ник на {new_nickname}"
