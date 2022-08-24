class RequestError(Exception):
    """Ошибка при отправке запроса к сервису ЯП."""


class StatusCodeError(Exception):
    """Ошибка доступа к сервису ЯП."""


class ApiResponseNotDictError(Exception):
    """Ошибка в данных сервиса - Ответ не представляет собой словарь."""


class ApiResponseNotListError(Exception):
    """Ошибка в данных сервиса - Ответ не представляет собой список."""


class ApiResponseError(Exception):
    """Ошибка в данных сервиса ЯП."""


class DenyOfServiceError(Exception):
    """Отказ в обслуживании от ендпоинта."""
