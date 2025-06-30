# Telegram Bot Skeleton

![GHCR pulls](https://img.shields.io/badge/ghcr-pulls-blue)
![Docker Publish](https://github.com/myorg/tgbot/actions/workflows/ci.yml/badge.svg)
![Version](https://img.shields.io/badge/version-1.1.0--alpha-green)

## Development

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Set up pre-commit hooks:

```bash
pre-commit install
```

Run tests:

```bash
pytest -q
```

## Database

The bot stores data in a SQLite file. Set the location via the `DB_PATH` variable
(default `/app/data/bot.db`). Tables are created by `init_db()` from
`bot/database.py` with foreign keys enabled using `PRAGMA foreign_keys=ON`.

## Authorization

When a new user sends `/start`, the bot records the request and notifies the chat defined in `ADMIN_CHAT_ID`. Until the admin approves the user, any commands besides `/start` are ignored.

## Context management & limits

Messages for each chat are stored in an in-memory buffer. The number of stored pairs is controlled by `MAX_CONTEXT_MESSAGES` (default 20). Command `/clear` wipes the history for the chat. Answers longer than 4096 characters are automatically split before sending.

## Supported LLM providers

| name    | image | audio | text/PDF | env vars |
|---------|-------|-------|----------|--------------------------------------|
| gemini  | ✓     | ✓     | ✓        | `GEMINI_API_KEY` |
| mistral | ✗     | ✗     | ✗        | `MISTRAL_API_KEY` |
| deepseek | ✗     | ✗     | ✗        | `DEEPSEEK_ENDPOINT`, `DEEPSEEK_API_KEY` |

List available models with `/models` or switch provider via `/providers`.

## 🔄 Переключение провайдера и модели

1. Выполните команду `/providers` и выберите нужный пункт.
2. Затем `/models` покажет список моделей активного провайдера.
3. Выбранные параметры сохраняются для каждого пользователя отдельно.

## File handling

Uploaded documents are saved to the directory defined by `FILES_DIR` (default
`./data/files`). Only models with ``supports_files`` can process files. Gemini
supports images, audio and text/PDF files when using the 1.5 Pro model.
Maximum size is 512 kB.

## Model auto-refresh

The bot uses APScheduler to update the `models` table on a schedule defined by
`REFRESH_CRON` (default `0 0 * * *`). New models detected across providers are
reported to the chat specified in `ADMIN_CHAT_ID`. Set `ENABLE_SCHEDULER=0` to
disable the job.

## Admin commands

The chat defined in `ADMIN_CHAT_ID` gains extra commands:

```
/admin stats            - show user and request counts
/admin users pending    - list pending approvals
/admin disable <id>     - revoke access for a user
/admin enable <id>      - re-enable user access
/admin models           - list stored models
/admin refresh models   - pull latest models from providers
```

## Docker / Compose

Quick start:

```bash
make dev   # build + run development stack
make prod  # run production stack
```
Example `.env`:
```env
BOT_TOKEN=...
ADMIN_CHAT_ID=999
DB_PATH=/app/data/bot.db
```

## Observability

Logs are emitted in JSON format using `structlog`. Example entry:

```json
{"event": "bot_started", "level": "info", "version": "1.1.0-alpha"}
```

Configure log level via `LOG_LEVEL` (default `INFO`). To send errors to Sentry
set `SENTRY_DSN`. All uncaught exceptions are logged and a short message is sent
to the chat defined by `ADMIN_CHAT_ID`.

## 🚑 Ошибки и fallback

При сбое провайдера пользователь получает сообщение:

```
⚠️ Не удалось получить ответ от модели gemini-pro. Попробуйте выбрать другую модель.
```

К сообщению прикрепляется кнопка «📋 Модели» для выбора альтернативной. Сводку
ошибок за последние 24 часа можно запросить командой `/admin errors` (доступно
только администратору).
