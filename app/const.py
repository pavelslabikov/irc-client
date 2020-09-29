HELP_MESSAGE = "| /add | Добавить текущий сервер в список избранного. | \n\
| /nick NICKNAME | Сменить ник на NICKNAME. | \n\
| /pm TARGET TEXT | Отправить персональное сообщение (TEXT) пользователю, каналу или сервис-боту (TARGET). |\n\
| /server HOSTNAME [PORT] | Подключиться к серверу с указанными HOSTNAME и PORT (по умолчанию 6667). |\n\
| /disconnect | Отключиться от сервера. |\n\
| /chcp CODEPAGE| Изменить текущую кодировку на CODEPAGE. |\n\
| /fav | Показать список избранных серверов. |\n\
| /names | Вывести список пользователей на активном канале. |\n\
| /list | Вывести список всех каналов на сервере. |\n\
| /join CHANNEL | Присоединиться к каналу CHANNEL (не должны быть уже присоединены к нему). |\n\
| /leave | Покинуть активный канал. |\n\
| /switch CHANNEL | Переключить активный канал на CHANNEL (должны быть присоединены к нему). |\n\
| /exit | Выход из приложения. |"

DEFAULT_CONFIG = {
    "Settings": {"nickname": "undefined", "codepage": "cp1251"},
    "Servers": {}
}

CONFIG_PATH = "config.ini"

BUFFER_SIZE = 4096
