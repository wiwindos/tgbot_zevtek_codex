### Итерация 0 — Project Bootstrap & CI Skeleton

*(подробный чек-лист для Codex; реальный код писать не нужно, здесь только шаги)*

> **Контекст репозитория:**
>
> * Уже есть минимальный бот (`bot/main.py`) с `/start`-хендлером и фабрикой `create_bot_and_dispatcher` .
> * Существуют юнит-тесты для `/start` (`tests/test_start.py`) .
> * Есть рабочий CI workflow (`ci.yml`) со сборкой тестов, но без линтинга и docker-dry-run .
> * Requirements уже заведён .

Ниже — шаги, которые ещё предстоит выполнить, чтобы достроить полный «Iteration 0».

---

#### 1. **T — Test First**

1. **Создать новый смоук-тест** `tests/test_smoke.py` (парадигма «красный-зелёный»):

   * Проверяет, что команда `/ping` возвращает ровно строку **«Bot ready»**.
   * Использовать тот же приём мокирования `Message.answer`, что уже реализован в `tests/test_start.py`, чтобы не делать реальный HTTP-вызов.
   * Запуск `pytest` сейчас должен упасть, потому что `/ping` ещё нет.

---

#### 2. **F — Feature**

1. **Добавить новый хендлер `/ping`** в существующий `bot/main.py`:

   * Ответ «Bot ready» (одной строкой, без эмодзи — это важно для теста).
   * Можно подключить к уже созданному `Dispatcher`, не меняя `/start`.
2. **CLI-режим "здоровье"**:

   * Дописать в `bot/main.py` (или отдельном `cli.py`) поддержку флага `--ping`.
   * При вызове `python -m bot.main --ping` скрипт должен:

     * инициализировать переменные окружения (через `python-dotenv`),
     * вывести «pong» в stdout,
     * завершиться с кодом 0.
3. **`.env.example`**:

   * Создать файл-шаблон с ключом `BOT_TOKEN=` и краткой инструкцией «скопируйте в .env».
4. **Зависимости**:

   * В `requirements.txt` указать ещё `python-dotenv`, `black`, `isort`, `flake8`, `mypy`, `pre-commit` (если их нет).
5. После реализации — убедиться, что новый смоук-тест и старый тест `/start` оба проходят (`pytest -q`).

---

#### 3. **I — Integrate**

1. **pre-commit**:

   * Сгенерировать `.pre-commit-config.yaml` с хуками **black**, **isort**, **flake8**, **mypy**.
   * Добавить команду установки в `README` (или Makefile).
2. **Расширить GitHub Actions** (`ci.yml`):

   * **Lint**-джоб: `pre-commit run --all-files`.
   * **Docker dry-run**: сборка образа `docker build -t bot:test .` (без пуша).
   * Упорядочить шаги: `checkout → setup-python → pip install → lint → tests → docker build`.
3. **Миграция существующего workflow**: убедиться, что новые шаги не ломают старый тестовый пайплайн.

---

#### 4. **P — Push**

1. Создать коммит c сообщением по Conventional Commits:

   ```
   feat(core): bootstrap ping command and CI linters
   ```
2. Открыть pull-request; убедиться, что CI зелёный (lint+tests+docker-dry-run).
3. Мерж в `main`.

---

#### Итог, который должен получить следующий этап:

| Артефакт              | Состояние после Iter 0 |
| --------------------- | ---------------------- |
| `/ping` командa       | отвечает «Bot ready»   |
| `tests/test_smoke.py` | зелёный                |
| `.env.example`        | создан                 |
| pre-commit + линтеры  | настроены              |
| CI (`ci.yml`)         | lint + tests + docker  |
| Dockerfile (базовый)  | собирается без ошибок  |

Теперь репозиторий полностью соответствует целям Bootstrap-итерации и готов к переходу к Iteration 1 («Database Schema with aiosqlite»).
