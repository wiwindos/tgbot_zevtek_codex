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

### File

* Поля:
  * `id: INTEGER PRIMARY KEY`
  * `request_id: INTEGER` — FK на `requests.id`
  * `path: TEXT` — путь к сохранённому файлу
  * `mime: TEXT`
  * `uploaded_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
* Таблица `files`.

### Model

* Поля:
  * `id: INTEGER PRIMARY KEY`
  * `provider: TEXT`
  * `name: TEXT`
  * `updated_at: TIMESTAMP`
* Таблица `models`.

### Error

* Поля:
  * `id: INTEGER PRIMARY KEY`
  * `provider: TEXT`
  * `model: TEXT`
  * `error: TEXT`
  * `created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
* Таблица `errors` собирает сбои провайдеров.

### Setting

* Поля:
  * `key: TEXT PRIMARY KEY`
  * `value: TEXT`
* Таблица `config` хранит вспомогательные параметры.

## 2. Структура модулей

| Модуль       | Описание                        | Файлы и папки                                                    |
| ------------ | ------------------------------- | ---------------------------------------------------------------- |
| **bot-core** | Логика Telegram-бота            | `main.py` (`start_handler`, `help_handler`, `ping_handler`, `create_bot_and_dispatcher`, `main`), `conversation.py`, `file_handlers.py`, `utils.py` |
| **database** | Инициализация и миграции БД     | `database.py` (`init_db`, `get_db`, `log_request`, `log_response`, `log_file`, `CREATE_USERS`, `CREATE_REQUESTS`, `CREATE_RESPONSES`, `CREATE_MODELS`, `CREATE_FILES`) |
| **services** | Бизнес-логика пользователей и LLM | `services/user_service.py`, `services/llm_service.py`, `AuthMiddleware`, `ContextBuffer`, `admin_router` |
| **file utils** | Проверка размера и MIME | `services/file_service.py` |
| **providers** | Абстракции LLM-провайдеров | `providers/base.py`, `gemini.py`, `mistral.py`, `deepseek.py`, `registry.py` |
| **scheduler** | Периодические задачи обновления моделей | `scheduler/jobs.py`, `scheduler/runner.py` |
| **tests**    | Юнит- и E2E-тесты               | `tests/conftest.py`, `tests/test_start.py`, `tests/test_help.py`, `tests/test_smoke.py`                       |
| **config**   | Конфигурация окружения          | `.env` (переменная `BOT_TOKEN`), `.env.example`                                  |
| **CI/CD**    | Настройка сборки и тестирования | `.github/workflows/ci.yml`                                       |
| **deps**     | Зависимости проекта             | `requirements.txt`, `requirements-dev.txt`                                               |
| **logging**  | Структурированный вывод и перехват ошибок | `logging_config.py`, `bot/error_middleware.py` |

## 3. Навигация для агентов

* **Изменить логику команд бота:** см. `main.py`, функции `start_handler` и регистрация команд в `create_bot_and_dispatcher()`.
* **Добавить новые поля в User:** редактируйте `CREATE TABLE users` в `database.py` и обновляйте `init_db()`.
* **Тесты на новые функции бота:** добавляйте файлы в папку `tests/`, используйте `pytest` и мок `BOT_TOKEN` через `conftest.py`.
* **CI-пайплайн:** для проверки lint, тестов и автодеплоя смотрите `.github/workflows/ci.yml`.

* **Контекст переписки:** `ContextBuffer` хранит историю сообщений,
  выбранный провайдер (`set_provider/get_provider`) и модель
  (`set_model/get_model`). Историю можно очистить командой `/clear`
  (также доступен алиас `/new`) без сброса выбранных параметров.
  При превышении суммарного объёма переписки 1000 символов бот один раз
  напомнит очистить историю.

```
User -> provider -> model
```
* **Админ-команды:** через `admin_router` доступны `stats`, `users pending`, `models`, `refresh models`, `disable/enable <id>`.
* **Обработка файлов:** `file_handlers.py` сохраняет присланные документы в `FILES_DIR` и передаёт их содержимое в LLM при поддержке модели.
  `GeminiProvider` кодирует изображения и аудио в base64 и поддерживает PDF/текст
  размером до 512 kB.

> **Важно:** актуализируйте этот файл при расширении модели данных или изменении структуры проекта.

## 4. Деплой

* Dockerfile теперь многоступенчатый: этап `builder` собирает и тестирует код, `runtime` содержит только продовые зависимости.
* `deploy/docker-compose.dev.yml` собирает builder-образ, `docker-compose.prod.yml` использует образ из GHCR.
* `scripts/entrypoint.sh` инициализирует БД перед запуском бота, путь задаётся переменной `DB_PATH` (по умолчанию `/app/data/bot.db`).
* Makefile содержит цели `dev` и `prod` для запуска соответствующих compose-стеков.
* Docker-тесты помечены маркером `docker` и автоматически пропускаются в CI.

