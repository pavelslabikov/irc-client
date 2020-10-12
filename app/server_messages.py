import abc
import re


class ServerMessage(abc.ABC):
    expr = re.compile("")

    def __init__(self, raw_message: str):
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
    expr = re.compile(r":(?P<nick>[^\s!]+)!?\S+ JOIN.* :?(?P<channel>\S+)")

    def parse_from_str(self, match) -> str:
        nickname = match.groupdict()["nick"]
        channel = match.groupdict()["channel"]
        return f"{nickname} присоединился к {channel}"


class PartMessage(ServerMessage):
    expr = re.compile(r":(?P<nick>[^\s!]+)!?\S+ PART.* :?(?P<channel>\S+)")

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
    expr = re.compile(r":(?P<nick>[^\s!]+)!?\S+ MODE.* :?(?P<mode>\S+)")  # TODO сменить регулярку

    def parse_from_str(self, match) -> str:
        nickname = match.groupdict()["nick"]
        new_mode = match.groupdict()["mode"]
        return f"{nickname} сменил мод на {new_mode}"


class ServiceMessage(ServerMessage):
    expr = re.compile(r":(?P<sender>[^\s!]+)(!.*)? \d{3} .+ :(?P<text>.+)")  # TODO: сменить регулярку

    def parse_from_str(self, match) -> str:
        sender = match.groupdict()["sender"]
        text = match.groupdict()["text"]
        return f"[{sender}] >> {text}"


class NickMessage(ServerMessage):
    expr = re.compile(r":(?P<nick>[^\s!]+)!?\S+ NAME.* :?(?P<new_nick>\S+)")

    def parse_from_str(self, match) -> str:
        nickname = match.groupdict()["nick"]
        new_nickname = match.groupdict()["new_nick"]
        return f"{nickname} сменил ник на {new_nickname}"


class UnresolvedMessage(ServerMessage):
    def parse_from_str(self, match) -> str:
        pass

    def __str__(self):
        return self.raw_message

