# CONTEXT.md

Описание доменной модели и структуры модулей проекта

## 1. Доменная модель

### User

* Поля:

  * `id: INTEGER PRIMARY KEY` — уникальный идентификатор записи
  * `tg_id: INTEGER UNIQUE` — Telegram ID пользователя
  * `name: TEXT` — имя или никнейм пользователя
* Хранится в таблице `users` (создаётся в `database.py`).

> Пока единственная модель данных: добавляйте новые поля к User через миграции в `database.py`.

## 2. Структура модулей

| Модуль       | Описание                        | Файлы и папки                                                    |
| ------------ | ------------------------------- | ---------------------------------------------------------------- |
| **bot-core** | Логика Telegram-бота            | `main.py` (`start_handler`, `help_handler`, `ping_handler`, `create_bot_and_dispatcher`, `main`, `cli`) |
| **database** | Инициализация и миграции БД     | `database.py` (`init_db`, `CREATE_USERS`)                        |
| **tests**    | Юнит- и E2E-тесты               | `tests/conftest.py`, `tests/test_start.py`, `tests/test_help.py`, `tests/test_smoke.py`                       |
| **config**   | Конфигурация окружения          | `.env`, `.env.example` (переменная `BOT_TOKEN`)                                  |
| **CI/CD**    | Настройка сборки и тестирования | `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `Dockerfile`                                       |
| **deps**     | Зависимости проекта             | `requirements.txt`                                               |
| **docs**     | Описание разработки             | `README.md`                                            |

## 3. Навигация для агентов

* **Изменить логику команд бота:** см. `main.py`, функции `start_handler` и регистрация команд в `create_bot_and_dispatcher()`.
* **Добавить новые поля в User:** редактируйте `CREATE TABLE users` в `database.py` и обновляйте `init_db()`.
* **CLI-проверка:** `python -m bot.main --ping` выводит "pong".
* **Запуск lint:** `pre-commit run --all-files`.
* **Тесты на новые функции бота:** добавляйте файлы в папку `tests/`, используйте `pytest` и мок `BOT_TOKEN` через `conftest.py`.
* **CI-пайплайн:** для проверки lint, тестов и автодеплоя смотрите `.github/workflows/ci.yml`.

> **Важно:** актуализируйте этот файл при расширении модели данных или изменении структуры проекта.
