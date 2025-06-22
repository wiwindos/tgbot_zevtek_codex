# CONTEXT.md

Описание доменной модели и структуры модулей проекта

## 1. Доменная модель

### User

* Поля:

  * `id: INTEGER PRIMARY KEY` — уникальный идентификатор записи
  * `tg_id: INTEGER UNIQUE` — Telegram ID пользователя
  * `name: TEXT` — имя или никнейм пользователя
  * `is_active: INTEGER` — доступ к боту (0/1)
  * `requested_at: TIMESTAMP` — когда отправлена заявка
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

### File

* Поля:
  * `id: INTEGER PRIMARY KEY`
  * `request_id: INTEGER` — FK на `requests.id`
  * `path: TEXT` — путь к сохранённому файлу
  * `mime: TEXT` — тип содержимого
  * `uploaded_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
* Таблица `files`.

## 2. Структура модулей

| Модуль       | Описание                        | Файлы и папки                                                    |
| ------------ | ------------------------------- | ---------------------------------------------------------------- |
| **bot-core** | Логика Telegram-бота            | `main.py` (`start_handler`, `help_handler`, `ping_handler`, `create_bot_and_dispatcher`, `main`), `conversation.py`, `file_handlers.py`, `utils.py` |
| **database** | Инициализация и миграции БД     | `database.py` (`init_db`, `get_db`, `log_request`, `log_response`, `log_file`, `CREATE_USERS`, `CREATE_REQUESTS`, `CREATE_RESPONSES`, `CREATE_MODELS`, `CREATE_FILES`) |
| **services** | Бизнес-логика пользователей и LLM | `services/user_service.py`, `services/llm_service.py`, `AuthMiddleware`, `ContextBuffer`, `admin_router` |
| **providers** | Абстракции LLM-провайдеров | `providers/base.py`, `gemini.py`, `mistral.py`, `dipseek.py`, `registry.py` |
| **scheduler** | Периодические задачи обновления моделей | `scheduler/jobs.py`, `scheduler/runner.py` |
| **tests**    | Юнит- и E2E-тесты               | `tests/conftest.py`, `tests/test_start.py`, `tests/test_help.py`, `tests/test_smoke.py`                       |
| **config**   | Конфигурация окружения          | `.env` (переменная `BOT_TOKEN`), `.env.example`                                  |
| **CI/CD**    | Настройка сборки и тестирования | `.github/workflows/ci.yml`                                       |
| **deps**     | Зависимости проекта             | `requirements.txt`                                               |

## 3. Навигация для агентов

* **Изменить логику команд бота:** см. `main.py`, функции `start_handler` и регистрация команд в `create_bot_and_dispatcher()`.
* **Добавить новые поля в User:** редактируйте `CREATE TABLE users` в `database.py` и обновляйте `init_db()`.
* **Тесты на новые функции бота:** добавляйте файлы в папку `tests/`, используйте `pytest` и мок `BOT_TOKEN` через `conftest.py`.
* **CI-пайплайн:** для проверки lint, тестов и автодеплоя смотрите `.github/workflows/ci.yml`.

* **Контекст переписки:** `ContextBuffer` сохраняет последние сообщения чата; очистить историю можно командой `/clear`.

> **Важно:** актуализируйте этот файл при расширении модели данных или изменении структуры проекта.
