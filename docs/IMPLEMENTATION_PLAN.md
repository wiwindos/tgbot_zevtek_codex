### Итерация 9 — Docker, Compose & One-Click Deploy

*T – F – I – P-план; сверяется с репо после Iter 8*

---

#### Актуальное состояние

* Базовый Dockerfile без healthcheck и без неправавого пользователя.
* Отсутствует `.dockerignore`.
* В `deploy/docker-compose.dev.yml` указан устаревший ключ `version:` (Compose V2 игнорирует его и ругается).
* Тесты падают:

  1. При остановке образа через `docker stop` (контейнер уже удалён через `--rm`).
  2. Сервис по `docker-compose` не помечается `healthy` (нет корректного healthcheck или слушателя на `/ping`).

---

## 1. T — Test first

1. **Пропуск при отсутствии Docker-демона**
   — В начале теста-файла авто-фикстура, вызывающая `docker info` и `pytest.skip`, если демона нет.
2. **Тест «image builds & runs»**

   * **Убрать опцию `--rm`** при старте тестового контейнера, чтобы он дожидался явной остановки.
   * После проверки логов и/или healthcheck останавливать контейнер строго через `docker stop` + `docker rm`.
   * Делать проверку healthcheck (если задан) через `docker inspect --format='{{.State.Health.Status}}'`.
3. **Тест «docker-compose up»**

   * **Удалить ключ `version:`** из `docker-compose.dev.yml`, чтобы не получалось предупреждение.
   * Добавить service-level healthcheck, который ждёт HTTP 200 от `/ping`.
   * В тесте после `up -d --build` проверять именно статус `healthy` у контейнера, а не просто `running`.

---

## 2. F — Feature

1. **Dockerfile**

   * Переход на `python:3.11-slim`.
   * `ARG BUILD_ENV` для разделения установки зависимостей (dev vs prod).
   * Создание неправавого пользователя `bot` и переключение на него.
   * Кеширование слоя установки pip-зависимостей.
   * Открытие порта `8080`.
   * Добавление `HEALTHCHECK`, который посылает GET на `/ping` и ожидает 200.
   * `LABEL org.opencontainers.image.version=$VERSION`.
2. **.dockerignore**
   — Выключить из контекста сборки `__pycache__`, `tests/`, `.venv/`, `*.log`, `*.db`, `.env`.
3. **deploy/docker-compose.dev.yml**

   * **Убрать поле `version:`** (Compose V2 сам понимает схему).
   * Настроить сервис `bot` с:

     * `build: .` и монтированием `./data:/app/data`.
     * `env_file: .env` и `restart: unless-stopped`.
     * Публикацией порта `8080:8080`.
     * **Healthcheck**, проверяющим HTTP 200 на `/ping`.
4. **deploy/docker-compose.prod.yml**

   * Сервис `bot` на уже запушенном образе:

     * Переменные через `environment` (включая `TZ=Europe/Berlin`).
     * `restart: always`, публикация порта и такой же healthcheck.
5. **Entrypoint**
   — Вынести в `scripts/entrypoint.sh` логику инициализации БД и старта приложения; подключить через `ENTRYPOINT`.
6. **CI (GitHub Actions)**

   * Job **docker-test**:

     * Запустить сборку образа.
     * Запустить контейнер без `--rm`, дождаться `bot_started` в логах или статуса `healthy`.
     * Остановить и удалить контейнер вручную.
     * Поднять `docker compose -f deploy/docker-compose.dev.yml up -d --build`, проверить health и том `./data`, затем `down`.
   * Job **docker-publish** (needs: docker-test):

     * Логин в GHCR.
     * Сборка с тегом SHA и пуш.
     * На тэговые пуши — дополнительный `latest`.
   * Включить `docker/setup-buildx-action` (и по желанию `docker/setup-qemu-action`).
7. **Badges & Deploy button**

   * В README: бейдж CI, бейдж GHCR size/pulls.
   * Кнопка «Deploy to Railway» или generic (с `railway.json`).
8. **Makefile**

   * Цели: `compose-up`, `compose-down`, `docker-build`, `docker-push`.
9. **ENV изменения**
   — Везде прописать `TZ=Europe/Berlin`.
10. **Version label**
    — Пробросить `VERSION` в Dockerfile и поставить `LABEL org.opencontainers.image.version=$VERSION`.

---

## 3. I — Integrate

* **README**: подробно описать команды и переменные для dev/prod.
* **pre-commit**: добавить linтинг Dockerfile через hadolint.
* **CI**: убедиться, что Buildx настроен, и healthcheck/job пропускает тесты только при реально успешном образе.
* **Docs**: в `docs/deploy.md` шаги: clone → cp .env → `make compose-up` → проверка `/ping` → `make compose-down`.

---

## 4. P — Push

Коммит «ci(docker): исправил compose, healthcheck и тесты; добавил non-root, ENTRYPOINT и GHCR publish» и пуш в `main`.
