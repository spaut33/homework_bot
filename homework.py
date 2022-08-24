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

PRACTICUM_TOKEN = os.environ.get('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
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
ENV_SETUP_ERROR = (
    'Окружение сконфигурировано неверно, пропущены токены: {tokens}'
)
ERROR = 'Сбой в работе программы: {error}'
REQUEST_ERROR = (
    'Сбой при запросе к ендпоинту: {error} - {endpoint} - {params}'
)
STATUS_CODE_ERROR = (
    'Сбой при http-запросе к ендпоинту: {status_code} - {endpoint} - {params}'
)
DENY_OF_SERVICE = (
    'В ответе ендпоинта содержится ошибка: {error_code} - {endpoint} - '
    '- {params}'
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


def get_api_answer(current_timestamp):
    """Отправляет запрос на ендпоинт и получает данные."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        raise exceptions.RequestError(
            REQUEST_ERROR.format(
                error=error,
                endpoint=ENDPOINT,
                params=params
            ))
    status_code = response.status_code
    if status_code != HTTPStatus.OK:
        raise exceptions.StatusCodeError(
            STATUS_CODE_ERROR.format(
                status_code=status_code,
                endpoint=ENDPOINT,
                params=params,
            ))
    json = response.json()

    for error_code in ERROR_CODES:
        if error_code in json:
            raise exceptions.DenyOfServiceError(
                DENY_OF_SERVICE.format(
                    error_code=error_code,
                    endpoint=ENDPOINT,
                    params=params,
                ))
    return json


def check_response(response):
    """Проверяет данные, полученные в ответе ендпоинта."""
    if not isinstance(response, dict):
        raise TypeError(RESPONSE_NOT_DICT_ERROR.format(got=type(response)))
    if 'homeworks' not in response:
        raise ValueError(NO_HOMEWORK_ERROR)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(RESPONSE_NOT_LIST_ERROR.format(got=type(response)))
    return homeworks


def parse_status(homework):
    """Разбирает ответ API и формирует сообщение для отправки ботом."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in VERDICTS:
        raise KeyError(UNKNOWN_STATUS_ERROR.format(status=homework_status))
    return HW_STATUS_CHANGED.format(
        homework_name=homework_name, verdict=VERDICTS.get(homework_status)
    )


def check_tokens():
    """Проверяет переменные окружения."""
    tokens = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')
    missed_tokens = []
    for name in tokens:
        if not globals()[name] or globals()[name] is None:
            missed_tokens.append(name)
    if missed_tokens:
        logger.critical(ENV_SETUP_ERROR.format(tokens=missed_tokens))
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise KeyError
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logger.info(BOT_STARTED)
    last_error_msg = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                for homework in homeworks:
                    parse_status(homework)
                    send_message(bot, parse_status(homework))
                    current_timestamp = response.get(
                        'current_date', current_timestamp
                    )
        except Exception as error:
            message = ERROR.format(error=error)
            logger.exception(message)
            if message != last_error_msg:
                send_message(bot, message)
                last_error_msg = message
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
