### Итерация 9 — **Docker, Compose & One-Click Deploy**

*T – F – I – P-план; сверен с текущим кодом `wiwindos/tgbot_zevtek_codex` после Iter 8*

---

#### Текущее состояние репозитория

| Факт                                                                                                                                                    | Расположение               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| Есть минимальный **Dockerfile** (python:3.11-slim, копирует проект, `CMD ["python", "-m", "bot.main"]`).  Docker-сборка уже запускается «dry-run» в CI. | `Dockerfile`               |
| `.dockerignore` отсутствует.                                                                                                                            | —                          |
| Нет `docker-compose.yml`; база SQLite хранится на хосте.                                                                                                | —                          |
| GitHub Actions билдит образ, но не пушит в registry.                                                                                                    | `.github/workflows/ci.yml` |
| Нет Make/Helper-скрипта для локального запуска или кнопки «Deploy to …».                                                                                | —                          |

---

## 1. T — **Test first**

| Шаг                                 | Детали                                                                                                                                                                                                                                                                                                     |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Файл**                            | `tests/deploy/test_image.py`                                                                                                                                                                                                                                                                               |
| **Тест-кейс «image builds & runs»** | 1. Использовать `subprocess.run(["docker", "build", "-t", "tgbot:test", "."], check=True)`. <br>2. Запустить контейнер в detached-режиме с переменной `BOT_TOKEN="dummy"`, `ADMIN_CHAT_ID=1`, `LOG_LEVEL=WARNING`; <br>3. Через `docker logs` дождаться строки `bot_started`; <br>4. Остановить контейнер. |
| **Тест-кейс «docker-compose up»**   | Запуск `docker compose -f deploy/docker-compose.dev.yml up -d --build`; проверить, что сервис `bot` healthy и каталог `./data` на хосте появился.                                                                                                                                                          |
| Ожидание                            | Тесты упадут: нет `compose`, нет healthcheck, логи др.                                                                                                                                                                                                                                                     |

---

## 2. F — **Feature**

| №    | Задача                               | Файл / модуль                                                                                                                                                                                                                                                       |
| ---- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1  | **Финальный Dockerfile**             | • Использовать `python:3.11-slim`<br>• `ARG BUILD_ENV=prod` (dev = poetry, prod = pip).<br>• Создать юзера `bot` (non-root).<br>• Копировать только нужные файлы, слой кеша для `requirements.txt`.<br>• Healthcheck: `CMD ["python", "-m", "bot.main", "--ping"]`. |
| 2.2  | **.dockerignore**                    | Добавить `__pycache__/`, `tests/`, `.venv/`, `*.log`, `*.db`…                                                                                                                                                                                                       |
| 2.3  | **`deploy/docker-compose.dev.yml`**  | Сервисы:<br>• `bot`: build `.`; volumes: `./data:/app/data`; env\_file: `.env`; restart: unless-stopped; healthcheck `curl -f http://localhost:8080/ping \|\| exit 1` (используем aiogram webhook OFF, поэтому просто `CMD --ping`).                                |
| 2.4  | **`deploy/docker-compose.prod.yml`** | Отличия: • image `ghcr.io/<OWNER>/tgbot:latest`; • environment вместо env\_file; • restart always.                                                                                                                                                                  |
| 2.5  | **Entrypoint-wrap**                  | `scripts/entrypoint.sh`:<br>`bash<br>python -m bot.database --init && python -m bot.main<br>`                                                                                                                                                                       |
| 2.6  | **GitHub Actions: build-push**       | Файл `ci.yml` → добавить job `docker-publish`:<br>• триггер `push tags` + `main`.<br>• Login `ghcr.io`.<br>• Build `docker build -t ghcr.io/${{github.repository_owner}}/tgbot:${{github.sha}} .`.<br>• Push latest on tag.                                         |
| 2.7  | **Badges & Deploy buttons**          | • README — badge GHCR size, badge CI.<br>• Кнопка «Deploy to Railway» (`railway.json`) или generic.                                                                                                                                                                 |
| 2.8  | **Makefile**                         | Targets: `make compose-up`, `compose-down`, `docker-build`, `docker-push`.                                                                                                                                                                                          |
| 2.9  | **ENV изменения**                    | Добавить `TZ=Europe/Berlin`.                                                                                                                                                                                                                                        |
| 2.10 | **Version label**                    | Добавить `LABEL org.opencontainers.image.version=$VERSION` в Dockerfile.                                                                                                                                                                                            |

---

## 3. I — **Integrate**

| Действие       | Детали                                                                                                      |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| **README**     | Раздел «Docker / Compose»: команды запуска dev и prod; переменные окружения; использование volume `./data`. |
| **pre-commit** | Добавить `hadolint` hook (Dockerfile lint).                                                                 |
| **CI**         | Установить `docker/setup-qemu-action` и `docker/setup-buildx-action` — build multi-arch.                    |
| **Docs**       | В `docs/deploy.md` шаг-за-шагом: *clone → cp .env → docker compose up -d*.                                  |

---

## 4. P — **Push**

```bash
git add .
git commit -m "ci(docker): production-ready Dockerfile, compose configs and GHCR publishing"
git push origin master
```

---

### Итог Iter 9

| Артефакт                              | Состояние                                 |
| ------------------------------------- | ----------------------------------------- |
| Production-grade **Dockerfile**       | неблокирующие кеши, non-root, healthcheck |
| `.dockerignore`                       | исключает лишнее                          |
| `docker-compose.dev.yml` / `prod.yml` | локальный dev и one-click prod            |
| GH Actions `docker-publish`           | пушит в GHCR                              |
| `tests/deploy/*`                      | сборка образа + compose healthcheck PASS  |
| README / docs / Makefile              | пошаговый deploy                          |
| CI / pre-commit                       | lint + build + push зелёные               |
