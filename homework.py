import json
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

PRACTICUM_TOKEN = os.environ.get('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

RETRY_TIME = 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}
HW_STATUS_CHANGED = (
    'Изменился статус проверки работы "{homework_name}". {verdict}'
)
ENV_SETUP_ERROR = 'Переменные окружения .env сконфигурированы неверно'
ERROR = 'Сбой в работе программы: {error}'
REQUEST_ERROR = 'Сбой при запросе к ендпоинту: {error}'
HTTP_ERROR = 'Сбой при http-запросе к ендпоинту: {status_code}'
TIMEOUT_ERROR = 'Таймаут http-запроса к ендпоинту: {error}'
JSON_ERROR = 'Ошибка в расшифровке json: {error}'
RESPONSE_ERROR = 'Неверные данные в ответе сервиса ЯП'
RESPONSE_NOT_DICT_ERROR = (
    'Данные в ответе сервиса ЯП не представляют собой словарь'
)
RESPONSE_NOT_LIST_ERROR = (
    'Данные в ответе сервиса ЯП не представляют собой список'
)
NO_NAME_ERROR = 'В ответе сервиса ЯП не содержится имя домашней работы'
NO_STATUS_ERROR = 'В ответе сервиса ЯП не содержится статуса домашней работы'
UNKNOWN_STATUS_ERROR = (
    'В ответе сервися ЯП содержится недокументированный статус домашней работы'
)
SUCCESS_SEND = 'Сообщение для юзера {chat_id} отправлено: {message}'
ERROR_SEND = (
    'Сообщение {message} для юзера {chat_id} не было отправлено: {error}'
)


def send_message(bot, message):
    """Отправляет сообщение через бота."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(
            SUCCESS_SEND.format(chat_id=TELEGRAM_CHAT_ID, message=message)
        )
    except Exception as error:
        logger.error(
            ERROR_SEND.format(
                chat_id=TELEGRAM_CHAT_ID, message=message, error=error
            )
        )


def get_api_answer(current_timestamp):
    """Отправляет запрос на ендпоинт и получает данные."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        logger.error(REQUEST_ERROR.format(error=error))
    except requests.exceptions.Timeout as error:
        logger.error(TIMEOUT_ERROR.format(error=error))
    status_code = response.status_code
    if status_code != HTTPStatus.OK:
        logger.error(HTTP_ERROR.format(status_code=status_code))
        raise exceptions.HTTPError

    try:
        return dict(response.json())
    except json.JSONDecodeError as error:
        logger.error(JSON_ERROR.format(error=error))
        raise exceptions.JSONDecodeError


def check_response(response):
    """Проверяет данные, полученные в ответе ендпоинта."""
    if not isinstance(response, dict):
        logger.error(RESPONSE_NOT_DICT_ERROR)
        raise TypeError(RESPONSE_NOT_DICT_ERROR)
    if 'current_date' and 'homeworks' not in response:
        logger.error(RESPONSE_ERROR)
        raise exceptions.ApiResponseError
    try:
        homeworks = response.get('homeworks')
    except KeyError:
        logger.error(RESPONSE_ERROR)
        raise KeyError(RESPONSE_ERROR)
    if not isinstance(homeworks, list):
        logger.error(RESPONSE_NOT_LIST_ERROR)
        raise TypeError(RESPONSE_NOT_LIST_ERROR)
    return homeworks


def parse_status(homework):
    """Разбирает ответ API и формирует сообщение для отправки ботом."""
    if 'homework_name' not in homework:
        logger.error(NO_NAME_ERROR)
        raise KeyError(NO_NAME_ERROR)

    homework_name = homework.get('homework_name')

    if 'status' not in homework:
        logger.error(NO_STATUS_ERROR)
        raise KeyError(NO_STATUS_ERROR)

    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        logger.error(UNKNOWN_STATUS_ERROR)
        raise exceptions.ResponseStatusError(UNKNOWN_STATUS_ERROR)

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return HW_STATUS_CHANGED.format(
        homework_name=homework_name, verdict=verdict
    )


def check_tokens():
    """Проверяет переменные окружения."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(ENV_SETUP_ERROR)
        raise exceptions.EnvironmentSetupError

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_error_msg = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            if homeworks:
                send_message(bot, parse_status(homeworks[0]))

            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = ERROR.format(error=error)
            logger.error(message)
            if message != last_error_msg:
                last_error_msg = message
                send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
