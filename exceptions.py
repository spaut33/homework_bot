class EnvironmentSetupError(Exception):
    """Ошибка в конфигурации переменных окружения"""


class JSONDecodeError(Exception):
    """Ошибка декодирования JSON-ответа от сервера."""


class ResponseStatusError(Exception):
    """Ошибка в статусе домашней работы."""


class HTTPError(Exception):
    """Ошибка доступа к сервису ЯП."""


class ApiResponseNotDictError(Exception):
    """Ошибка в данных сервиса - Ответ не представляет собой словарь."""


class ApiResponseNotListError(Exception):
    """Ошибка в данных сервиса - Ответ не представляет собой список."""


class ApiResponseError(Exception):
    """Ошибка в данных сервиса ЯП."""
