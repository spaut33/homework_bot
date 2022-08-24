# 🤖 Homework Bot - Telegram bot для проверки статуса домашней работы



<img alt="Python" src="https://img.shields.io/badge/Python-100%25-blue?style=flat&logo=python">

## Содержание

- [Описание](#Описание)
- [Установка](#Установка)
- [Использование](#Использование)
- [Вклад](#Вклад)
- [Инструкции для тестирования](#Инструкции-для-тестирования)
- [Лицензия](#Лицензия)
- [Контактная информация](#Контактная-информация)

## Описание

`Homework Bot` присылает сообщение в мессенджер Telegram при смене статуса проверки домашней работы.
Создан специально для курса Python Backend+ @ Яндекс Практикуме, но может использоваться и с другими
курсами ЯП.

Бот использует данные <a href="https://practicum.yandex.ru/api/user_api/homework_statuses/">API Яндекс Практикума</a>.
(<a href="https://code.s3.yandex.net/backend-developer/learning-materials/delugov/%D0%9F%D1%80%D0%B0%D0%BA%D1%82%D0%B8%D0%BA%D1%83%D0%BC.%D0%94%D0%BE%D0%BC%D0%B0%D1%88%D0%BA%D0%B0%20%D0%A8%D0%BF%D0%B0%D1%80%D0%B3%D0%B0%D0%BB%D0%BA%D0%B0.pdf">Инструкция по эксплуатации АПИ</a>.)


Проект написан на Python 3.7+ и использует библиотеку <a href="https://github.com/python-telegram-bot/python-telegram-bot">python-telegram-bot</a>


## Установка

###### 📣 Перед установкой этого проекта, убедитесь что у вас установлен Python (3.7+)
###### 📣 У вас должен быть токен авторизации Яндекса для доступа к АПИ (см. .env.example)
###### 📣 У вас должен быть создан бот в месенджере телеграм (см. .env.example)

- клонировать репозиторий: `git clone git@github.com:spaut33/homework_bot.git`
- сменить директорию (необходимо быть в рабочей директории репозитория) например: `cd homework_bot`
- сконфигурировать виртуальное окружение `python3 -m venv .venv`
- активировать его `source /.venv/Scripts/activate`
- установить зависимости `pip install -r requirements.txt`
- создать файл .env с переменными окружения по примеру из файла .env.example

## Использование

Запустить бота командой

```python homework.py```

## Вклад

Если вы хотите сделать вклад в этот проект, свяжитесь со мной. Контактная информация есть ниже.

## Инструкции для тестирования

Этот проект покрыт тестами, для запуска `pytest`

## Лицензия

<a href="https://img.shields.io/badge/License-MIT-brightgreen?style=flat"><img alt="M.I.T. License use" src="https://img.shields.io/badge/License-MIT-brightgreen"></a>

## Контактная информация

Email: roman.petrakov@gmail.com

[Роман Петраков @ github](https://github.com/spaut33)