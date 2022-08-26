import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

logger = logging.getLogger(__name__)

TOKENS = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')
PRACTICUM_TOKEN = os.environ.get(TOKENS[0])
TELEGRAM_TOKEN = os.environ.get(TOKENS[1])
TELEGRAM_CHAT_ID = os.environ.get(TOKENS[2])
RETRY_TIME = 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}
HW_STATUS_CHANGED = (
    'Изменился статус проверки работы "{homework_name}". {verdict}'
)
MISSED_TOKENS = (
    'Окружение сконфигурировано неверно, пропущены токены: {tokens}'
)
ENV_SETUP_ERROR = 'Окружение сконфигурировано неверно'
ERROR = 'Сбой в работе программы: {error}'
REQUEST_ERROR = (
    'Сбой при запросе к ендпоинту: {error} - {url} - {params} - {headers}'
)
STATUS_CODE_ERROR = (
    'Сбой при http-запросе к ендпоинту: {status_code} - {url} - {params}'
    ' - {headers}'
)
DENY_OF_SERVICE = (
    'В ответе ендпоинта содержится ошибка: {error_code} - {error} - '
    '{url} - {params} - {headers}'
)
NO_HOMEWORK_ERROR = 'В ответе сервиса ЯП нет данных о дамашних работах'
RESPONSE_NOT_DICT_ERROR = 'В ответе ожидается словарь, а получен {got}'
RESPONSE_NOT_LIST_ERROR = 'В ответе ожидается список, а получен {got}'
UNKNOWN_STATUS_ERROR = (
    'В ответе сервися ЯП содержится недокументированный '
    'статус домашней работы: {status}'
)
SUCCESS_SEND = 'Сообщение для юзера {chat_id} отправлено: {message}'
ERROR_SEND = (
    'Сообщение {message} для юзера {chat_id} не было отправлено: {error}'
)
BOT_STARTED = 'Бот начал свою работу'
ERROR_CODES = ('error', 'code')


def send_message(bot, message):
    """Отправляет сообщение через бота."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(
            SUCCESS_SEND.format(chat_id=TELEGRAM_CHAT_ID, message=message)
        )
    except Exception as error:
        logger.exception(
            ERROR_SEND.format(
                chat_id=TELEGRAM_CHAT_ID, message=message, error=error
            )
        )
    return True


def get_api_answer(current_timestamp):
    """Отправляет запрос на ендпоинт и получает данные."""
    params = dict(
        url=ENDPOINT,
        params={'from_date': current_timestamp},
        headers=HEADERS,
    )
    try:
        response = requests.get(**params)
    except requests.exceptions.RequestException as error:
        raise ConnectionError(REQUEST_ERROR.format(error=error, **params))
    status_code = response.status_code
    if status_code != HTTPStatus.OK:
        raise exceptions.StatusCodeError(
            STATUS_CODE_ERROR.format(status_code=status_code, **params)
        )
    json = response.json()
    for error_code in ERROR_CODES:
        if error_code in json:
            raise exceptions.DenyOfServiceError(
                DENY_OF_SERVICE.format(
                    error_code=error_code,
                    error=json[error_code],
                    **params
                ))
    return json


def check_response(response):
    """Проверяет данные, полученные в ответе ендпоинта."""
    if not isinstance(response, dict):
        raise TypeError(RESPONSE_NOT_DICT_ERROR.format(got=type(response)))
    if 'homeworks' not in response:
        raise ValueError(NO_HOMEWORK_ERROR)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(RESPONSE_NOT_LIST_ERROR.format(got=type(homeworks)))
    return homeworks


def parse_status(homework):
    """Разбирает ответ API и формирует сообщение для отправки ботом."""
    name = homework['homework_name']
    status = homework['status']
    if status not in VERDICTS:
        raise ValueError(UNKNOWN_STATUS_ERROR.format(status=status))
    return HW_STATUS_CHANGED.format(
        homework_name=name, verdict=VERDICTS[status]
    )


def check_tokens() -> bool:
    """Проверяет переменные окружения."""
    missed_tokens = [name for name in TOKENS if not globals()[name]]
    if missed_tokens:
        logger.critical(MISSED_TOKENS.format(tokens=missed_tokens))
    return not missed_tokens


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise ValueError(ENV_SETUP_ERROR)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logger.info(BOT_STARTED)
    last_error = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                continue
            if send_message(bot, parse_status(homeworks[0])):
                current_timestamp = response.get(
                    'current_date', current_timestamp
                )
        except Exception as error:
            message = ERROR.format(error=error)
            logger.exception(message)
            if send_message(bot, message) and message != last_error:
                last_error = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        format=(
            '%(asctime)s - %(name)s - %(levelname)s: %(funcName)s() l:'
            '%(lineno)d - %(message)s'
        ),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(__file__ + '.log', encoding='UTF-8'),
        ],
        level=logging.INFO,
    )
    main()

    # from unittest import TestCase, mock, main as uni_main
    # JSON = {"error":{"error":"Wrong from_date format"},"code":"UnknownError"}
    #
    #
    # class TestReq(TestCase):
    #     @mock.patch('requests.get')
    #     def test_error(self, rq_get):
    #         resp = mock.Mock()
    #         resp.json = mock.Mock(return_value=JSON)
    #         resp.status_code = 200
    #         rq_get.return_value = resp
    #         main()
    # uni_main()
