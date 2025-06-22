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
