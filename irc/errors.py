class ApiError(Exception):
    arg = ""


class InvalidConfigError(ApiError):
    def __init__(self, invalid_config):
        for key, value in invalid_config.items():
            self.arg += f"\n[{key}]\n"
            for option_key, option_value in value.items():
                self.arg += f"{option_key} = {option_value}\n"

    def __str__(self):
        return f"Некорректное содержимое файла config.ini: {self.arg}"


class ConfigNotFoundError(ApiError):
    def __init__(self, path: str):
        self.arg = path

    def __str__(self):
        return f"Не удалось найти файл config.ini в директории - {self.arg}"
