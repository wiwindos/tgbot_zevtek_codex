### Итерация 8 — **Observability & Error Handling**

*(T – F – I – P план; сверен с текущим состоянием `wiwindos/tgbot_zevtek_codex` после Iter 7)*

---

#### Текущее состояние репозитория

| Факт                                                                                                                      | Расположение                       |
| ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Клиент бота работает, middlewares `AuthMiddleware`, `ContextMiddleware` уже подключены.                                   | `bot/middleware.py`, `bot/main.py` |
| Логи пишутся простым `logging.basicConfig(level=INFO)`; формат — строковый, без JSON.                                     | `bot/main.py`                      |
| Нет глобального перехвата необработанных исключений; пользователь получает default error Telegram, админ не уведомляется. | —                                  |
| Файлов мониторинга / трассировки (Sentry, structlog) нет.                                                                 | —                                  |
| CI lint/tests/docker зелёные; pre-commit настроен.                                                                        | `.github/workflows/ci.yml`         |

---

## 1. **T — Test first**

| Шаг                            | Детали                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Файл**                       | `tests/integration/test_errors.py`                                                                                                                                                                                                                                                                                                                                |
| **Fixtures**                   | • tmp-DB; <br>• `ADMIN_CHAT_ID = 999`; <br>• patch `providers.GeminiProvider.generate` → `raise RuntimeError("gemini boom")`; <br>• capture `caplog` (pytest fixture) + мок `Bot.send_message`.                                                                                                                                                                   |
| **Тест-кейс «graceful error»** | 1. Отправить текст, выбранная модель — «gemini-pro».<br>2. Проверить: <br> a) пользователю бот отвечает «Что-то пошло не так, попробуйте позже» (friendly).<br> b) `Bot.send_message` в админ-чат вызван с текстом, содержащим `RuntimeError`.<br> c) `caplog.records` содержит JSON-лог с полем `"event": "unhandled_exception"` и `"exc_info": "RuntimeError"`. |
| **Ожидание**                   | Тест падает — нет middleware, нет JSON-логов, нет уведомления.                                                                                                                                                                                                                                                                                                    |

---

## 2. **F — Feature**

| №   | Задача                           | Файл / модуль                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 | **Структурный логгер**           | Добавить зависимость `structlog` и (опционально) `sentry-sdk` (`requirements.txt`).                                                                                                                                                                                                                                                                                                                                                                            |
| 2.2 | **`logging_config.py`**          | Новый модуль: функция `configure_logging(level: str = "INFO")`<br>• stdlib → structlog binding;<br>• JSON `processors=[structlog.processors.JSONRenderer()]`;<br>• читает `LOG_LEVEL` из env.                                                                                                                                                                                                                                                                  |
| 2.3 | **Инициализация**                | В начале `bot/main.py` вызвать `configure_logging()` до создания `Bot`.                                                                                                                                                                                                                                                                                                                                                                                        |
| 2.4 | **Middleware `ErrorMiddleware`** | `bot/error_middleware.py`:<br>`python<br>class ErrorMiddleware(BaseMiddleware):<br>    async def __call__(handler, event, data):<br>        try: return await handler(event, data)<br>        except Exception as exc:<br>            logger.exception(\"unhandled_exception\", exc_info=exc)<br>            await send_long_message(event.chat.id, \"Что-то пошло не так…\")<br>            await bot.send_message(ADMIN_CHAT_ID, f\"❗️ Ошибка: {exc}\")<br>` |
| 2.5 | **Подключить middleware**        | В `create_bot_and_dispatcher()` добавить `dp.message.middleware(ErrorMiddleware())` **первым** в цепочке.                                                                                                                                                                                                                                                                                                                                                      |
| 2.6 | **Sentry (опц.)**                | В `logging_config.configure_logging()`:<br>`python<br>dsn = os.getenv(\"SENTRY_DSN\")<br>if dsn: sentry_sdk.init(dsn, traces_sample_rate=0.1)<br>`                                                                                                                                                                                                                                                                                                             |
| 2.7 | **Health-лог**                   | При старте (`main.py`) лог `logger.info("bot_started", version=__version__)`.                                                                                                                                                                                                                                                                                                                                                                                  |
| 2.8 | **ENV-пример**                   | `.env.example` — добавить `LOG_LEVEL=INFO`, `SENTRY_DSN=`.                                                                                                                                                                                                                                                                                                                                                                                                     |

---

## 3. **I — Integrate**

| Действие       | Описание                                                                                                              |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| **README**     | Новый раздел “Observability”: пример JSON-лога, переменные `LOG_LEVEL`, `SENTRY_DSN`; как видеть ошибки в админ-чате. |
| **pre-commit** | mypy-strict `bot/error_middleware.py`, `logging_config.py`.                                                           |
| **CI**         | Dependabot-стиль: `pytest` уже захватит новый тест; Dockerfile — `pip install structlog sentry-sdk`.                  |
| **Док-строки** | В `ErrorMiddleware` подробно описать порядок обработки исключений.                                                    |

---

## 4. **P — Push**

```bash
git add .
git commit -m "feat(obs): structured JSON logging and global error middleware with admin alerts"
git push origin master
```

---

### Итог Iter 8

| Компонент / Функция                     | Состояние                                                   |
| --------------------------------------- | ----------------------------------------------------------- |
| `structlog` JSON-формат                 | настроен, вывод в stdout                                    |
| `ErrorMiddleware`                       | ловит все необработанные, отвечает юзеру + уведомляет админ |
| Sentry интеграция (env-опц.)            | работает при наличии `SENTRY_DSN`                           |
| Конфиг `LOG_LEVEL`                      | читается из .env                                            |
| Тест `tests/integration/test_errors.py` | зелёный                                                     |
| README / .env.example                   | обновлены                                                   |
| CI / Docker                             | проходят                                                    |

