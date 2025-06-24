### Итерация 10 — **“DB-Path Fix & Production-grade Docker”**

---

#### Текущее состояние репозитория

| Факт                                                                                                                                                                          | Найдено |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-----: |
| Контейнер стартует с томом `./data`, но приложение внутри ищет БД по относительному пути `./bot.db`, в итоге `OperationalError: unable to open database file` на чистом томе. |    ✓    |
| Указание `DB_PATH=/app/data/bot.db` уже прописано в **docker-compose**, однако код жёстко фиксирует путь.                                                                     |    ✓    |
| В корне один `Dockerfile`; каталог **`deploy/`** содержит compose-файлы, но лишних дубликатов Dockerfile нет.                                                                 |    ✓    |
| `requirements.txt` включает и run-time, и dev-зависимости (pytest, mypy, black …) — в проде они не нужны.                                                                     |    ✓    |

---

## 1. **T — Test first**

| Шаг                                  | Детали                                                                                                                                                                                                                                            |   |                                       |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | - | ------------------------------------- |
| **Файл**                             | `tests/deploy/test_first_run.py`                                                                                                                                                                                                                  |   |                                       |
| **Тест-кейс «db-init in container»** | 1. `docker compose -f deploy/docker-compose.dev.yml up -d --build bot` (новая сборка).<br>2. Ожидаем `health_status: healthy`, затем `docker exec bot ls /app/data/bot.db` → успех.<br>3. В контейнерных логах не должно быть `OperationalError`. |   |                                       |
| **Тест-кейс «no dev deps in prod»**  | 1. `docker build -t tgbot:prod --target runtime .`<br>2. \`docker run --rm tgbot\:prod pip show pytest                                                                                                                                            |   | true\` → выход без найденного пакета. |
| *Ожидание*                           | Оба теста падают — код и Dockerfile ещё не доработаны.                                                                                                                                                                                            |   |                                       |

---

## 2. **F — Feature**

| №   | Задача                          | Файл / модуль                                                                                                                                                                                                                                                                                                           |   |          |
| --- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | - | -------- |
| 2.1 | **Параметризуем путь БД**       | `database.py` — заменить константу на<br>`DB_PATH = Path(os.getenv("DB_PATH", "/app/data/bot.db"))`;<br>добавить `DB_PATH.parent.mkdir(parents=True, exist_ok=True)` перед подключением.                                                                                                                                |   |          |
| 2.2 | **.env.example**                | Добавить строку `DB_PATH=/app/data/bot.db`.                                                                                                                                                                                                                                                                             |   |          |
| 2.3 | **Разводим зависимости**        | • `requirements.txt` — только prod-библиотеки.<br>• `requirements-dev.txt` — prod + pytest, mypy, black и др.                                                                                                                                                                                                           |   |          |
| 2.4 | **Dockerfile v2 (multi-stage)** | **Stage “builder”** — устанавливает dev-deps, выполняет `pytest`/`mypy`.<br>**Stage “runtime”** — устанавливает лишь prod-deps, копирует исходники.<br>Дополнительно:<br> • `ENV DB_PATH=/app/data/bot.db`<br> • `VOLUME /app/data`<br> • non-root пользователь `bot`<br> • \`HEALTHCHECK CMD python -m bot.main --ping |   | exit 1\` |
| 2.5 | **Compose-файлы**               | `deploy/docker-compose.dev.yml` — `build.target: builder` (тесты в image).<br>`deploy/docker-compose.prod.yml` — `image: ghcr.io/<OWNER>/tgbot:latest` (runtime-layer).                                                                                                                                                 |   |          |
| 2.6 | **CI / GitHub Actions**         | Job `docker-publish` строит два таргета:<br>• `builder` — только build & тесты (не push).<br>• `runtime` — push в GHCR.                                                                                                                                                                                                 |   |          |
| 2.7 | **.dockerignore**               | Исключить: `tests/`, `.venv/`, `__pycache__/`, `*.db`, `*.log`, `deploy/`, `.git`, `.github`.                                                                                                                                                                                                                           |   |          |
| 2.8 | **Makefile helper**             | `make dev` → compose dev-стека; `make prod` → compose prod-стека.                                                                                                                                                                                                                                                       |   |          |
| 2.9 | **Удаляем дубли**               | В каталоге `deploy/` оставить только compose-файлы; убедиться, что Dockerfile один, в корне.                                                                                                                                                                                                                            |   |          |

---

## 3. **I — Integrate**

| Действие       | Детали                                                                                      |
| -------------- | ------------------------------------------------------------------------------------------- |
| **README**     | Обновить раздел *Quick start*: пример `.env` c `DB_PATH`, команды `make dev` / `make prod`. |
| **pre-commit** | Добавить хук проверки зависимостей (`pip-check`), хук `hadolint` для Dockerfile.            |
| **Docs**       | `docs/docker.md` — схема multi-stage, зачем два requirements-файла.                         |
| **CI-badge**   | README — добавить статус Docker publish.                                                    |

---

## 4. **P — Push**

```bash
git add .
git commit -m "build(docker): env-driven DB_PATH, split dev/prod deps и multi-stage image"
git push origin master
```

---

### Итог Iter 10

| Компонент / Функция       | Состояние после итерации                        |
| ------------------------- | ----------------------------------------------- |
| `DB_PATH` через env       | База создаётся в `/app/data/bot.db`, ошибок нет |
| Multi-stage Dockerfile    | `builder` (тесты) и `runtime` (prod < 200 MB)   |
| `requirements*.txt`       | dev-пакеты исключены из prod-образа             |
| Compose-файлы             | dev-target и prod-target, дублей нет            |
| Тесты `test_first_run.py` | зелёные                                         |
| CI (build + push)         | зелёный                                         |
| README / docs             | обновлены                                       |
