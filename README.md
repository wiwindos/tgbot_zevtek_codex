# Telegram Bot Skeleton

## Development

Install dependencies:

```bash
pip install -r requirements.txt
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

The bot uses a SQLite file `bot.db`. It is created by calling `init_db()` from
`bot/database.py`. Foreign key support is enabled via
`PRAGMA foreign_keys=ON` during initialization.

## Authorization

When a new user sends `/start`, the bot records the request and notifies the chat defined in `ADMIN_CHAT_ID`. Until the admin approves the user, any commands besides `/start` are ignored.

## Context management & limits

Messages for each chat are stored in an in-memory buffer. The number of stored pairs is controlled by `MAX_CONTEXT_MESSAGES` (default 20). Command `/clear` wipes the history for the chat. Answers longer than 4096 characters are automatically split before sending.

## Supported LLM providers

| name    | supports_files | env vars                             |
|---------|---------------|--------------------------------------|
| gemini  | true          | `GEMINI_PROJECT`, `GEMINI_LOCATION`, `GEMINI_KEY` |
| mistral | false         | `MISTRAL_API_KEY`                    |
| dipseek | false         | `DIPSEEK_ENDPOINT`, `DIPSEEK_API_KEY` |

## File handling

Uploaded documents are saved to the directory defined by `FILES_DIR` (default
`./data/files`). Only models with ``supports_files`` can process files. Gemini
currently supports file input.

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
