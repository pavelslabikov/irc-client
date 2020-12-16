import logging
import shlex
import irc.commands as com
from irc import messages


logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, client):
        self._client = client
        self.commands = {
            "/chcp": com.CodePageCommand,
            "/nick": com.NickCommand,
            "/help": com.HelpCommand,
            "/fav": com.ShowFavCommand,
            "/server": com.ConnectCommand,
            "/exit": com.ExitCommand,
            "/pm": com.WhisperCommand,
            "/add": com.AddFavCommand,
            "/join": com.JoinCommand,
            "/list": com.ListCommand,
            "/names": com.NamesCommand,
            "/leave": com.PartCommand,
            "/quit": com.QuitCommand,
            "/switch": com.SwitchCommand,
        }

    def get_command(self, input_text: str) -> com.ClientCommand:
        if input_text.startswith("/"):
            command_parts = shlex.split(input_text)
            command_name, command_args = command_parts[0], command_parts[1:]
            if command_name in self.commands:
                return self.commands[command_name](self._client, *command_args)

        elif self._client.current_channel and input_text.rstrip(" "):
            return com.WhisperCommand(
                self._client,
                self._client.current_channel,
                *input_text.split(" "),
            )

        logger.debug(f"Cannot parse command: {input_text}")
        return com.UnknownCommand(self._client)


class MessageHandler:
    def __init__(self, client):
        self.client = client
        self.messages = {
            "JOIN": messages.JoinMessage,
            "PART": messages.PartMessage,
            "NICK": messages.NickMessage,
            "MODE": messages.ModeMessage,
            "PRIVMSG": messages.PrivateMessage,
            "NOTICE": messages.NoticeMessage,
        }

    def get_messages(self, decoded_data: str) -> list:
        result = []
        for line in decoded_data.split("\r\n"):
            parts = line.split(" ")
            if len(parts) < 2:
                logger.debug(f"Received too short message: {line}")
                continue
            command_name = parts[1].upper()
            if command_name in self.messages:
                result.append(self.messages[command_name](self.client, line))
            elif command_name.isdigit():
                result.append(messages.ServiceMessage(self.client, line))
            else:
                logger.debug(f"Received unresolved message: {line}")
                continue
        return result
