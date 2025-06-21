# CONTEXT.md

Описание доменной модели и структуры модулей проекта

## 1. Доменная модель

### User

* Поля:

  * `id: INTEGER PRIMARY KEY` — уникальный идентификатор записи
  * `tg_id: INTEGER UNIQUE` — Telegram ID пользователя
  * `name: TEXT` — имя или никнейм пользователя
* Хранится в таблице `users` (создаётся в `database.py`).

### Request

* Поля:
  * `id: INTEGER PRIMARY KEY`
  * `user_id: INTEGER` — FK на `users.id`
  * `prompt: TEXT` — текст запроса
  * `model: TEXT` — название модели
  * `created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
* Таблица `requests`.

### Response

* Поля:
  * `id: INTEGER PRIMARY KEY`
  * `request_id: INTEGER` — FK на `requests.id`
  * `content: TEXT`
  * `created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
* Таблица `responses`.

### Model

* Поля:
  * `id: INTEGER PRIMARY KEY`
  * `provider: TEXT`
  * `name: TEXT`
  * `updated_at: TIMESTAMP`
* Таблица `models`.

## 2. Структура модулей

| Модуль       | Описание                        | Файлы и папки                                                    |
| ------------ | ------------------------------- | ---------------------------------------------------------------- |
| **bot-core** | Логика Telegram-бота            | `main.py` (`start_handler`, `help_handler`, `ping_handler`, `create_bot_and_dispatcher`, `main`) |
| **database** | Инициализация и миграции БД     | `database.py` (`init_db`, `get_db`, `log_request`, `log_response`, `CREATE_USERS`, `CREATE_REQUESTS`, `CREATE_RESPONSES`, `CREATE_MODELS`) |
| **tests**    | Юнит- и E2E-тесты               | `tests/conftest.py`, `tests/test_start.py`, `tests/test_help.py`, `tests/test_smoke.py`                       |
| **config**   | Конфигурация окружения          | `.env` (переменная `BOT_TOKEN`), `.env.example`                                  |
| **CI/CD**    | Настройка сборки и тестирования | `.github/workflows/ci.yml`                                       |
| **deps**     | Зависимости проекта             | `requirements.txt`                                               |

## 3. Навигация для агентов

* **Изменить логику команд бота:** см. `main.py`, функции `start_handler` и регистрация команд в `create_bot_and_dispatcher()`.
* **Добавить новые поля в User:** редактируйте `CREATE TABLE users` в `database.py` и обновляйте `init_db()`.
* **Тесты на новые функции бота:** добавляйте файлы в папку `tests/`, используйте `pytest` и мок `BOT_TOKEN` через `conftest.py`.
* **CI-пайплайн:** для проверки lint, тестов и автодеплоя смотрите `.github/workflows/ci.yml`.

> **Важно:** актуализируйте этот файл при расширении модели данных или изменении структуры проекта.
