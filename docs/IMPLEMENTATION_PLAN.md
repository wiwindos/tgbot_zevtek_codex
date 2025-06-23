### Итерация 9 — **Docker, Compose & One-Click Deploy**

*(обновлённый полный T – F – I – P-план; скорректирован под реальное дерево `wiwindos/tgbot_zevtek_codex`, при этом тяжёлые docker-тесты **никогда** не запускаются в GitHub Actions)*

---

#### Текущее состояние репозитория (v `master`)

| Факт                                                                                                                                                | Где видно                                                |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Имеется минимальный **Dockerfile** (копирует проект, запускает `python -m bot.main`), но: нет `HEALTHCHECK`, нет non-root-user, нет сетевого порта. | `Dockerfile`                                             |
| `.dockerignore` отсутствует → контекст сборки огромный.                                                                                             | —                                                        |
| Есть `deploy/docker-compose.dev.yml`, в котором задан устаревший ключ `version:`; health-check отсутствует.                                         | `deploy/…`                                               |
| В CI workflow `build` выполняется `pytest`, куда входят 2 docker-heavy теста, из-за чего пайплайн падает (GitHub runner ≠ privileged).              | `.github/workflows/ci.yml`, `tests/deploy/test_image.py` |
| Бот умеет отвечать на `--ping`, но внутри контейнера health-probe не настроен.                                                                      | `bot/main.py`                                            |

---

## 1  T — **Test first**

> Цель — оставить docker-тесты полезными локально, но гарантированно **пропустить** их в GitHub CI.

| Шаг | Действие                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.1 | **Маркируем** оба деплой-теста: в начале файлов `tests/deploy/test_image.py` и `test_compose.py` добавить `@pytest.mark.docker`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 1.2 | **Глобальный auto-skip** в `tests/conftest.py`:  `python<br>import os, pytest, subprocess<br><br>def pytest_configure(config):<br>    config.addinivalue_line(\"markers\", \"docker: tests that require local Docker daemon\")<br><br>def pytest_collection_modifyitems(config, items):<br>    ci = os.getenv(\"CI\", \"0\") == \"1\"  # GitHub sets CI=1<br>    daemon_up = subprocess.call([\"docker\", \"info\"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0<br>    if ci or not daemon_up:<br>        skip_it = pytest.mark.skip(reason=\"Docker tests skipped on CI or when daemon is absent\")<br>        for item in items:<br>            if \"docker\" in item.keywords:<br>                item.add_marker(skip_it)<br>` |
| 1.3 | **Правим сами тесты** (чтобы проходили локально):<br>• убрать `--rm` из `docker run`;<br>• health-status проверять через `docker inspect`;<br>• после проверки контейнер останавливать и удалять вручную.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

> ✅ На CI переменная `CI=1` → оба теста будут отмечены `skipped`, отчёт `pytest` покажет «skipped=2, failed=0».

---

## 2  F — **Feature**

| №       | Задача                                                                                                                                                                                                                                                                                                                                                                                                      | Файл / артефакт               |                                                                                                                         |              |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------ |
| **2.1** | **Dockerfile (production-grade)**<br>  \* python:3.11-slim.<br>  \* `WORKDIR /app`.<br>  \* `adduser --disabled-password --gecos \"\" bot` → `USER bot`.<br>  \* Кешируем слой `pip install -r requirements.txt` до `COPY . .`.<br>  \* Открываем порт `8080`.<br>  \* \`HEALTHCHECK --interval=30s --start-period=30s --retries=3 CMD python -m bot.main --ping                                            |                               | exit 1`.<br>  * `ENTRYPOINT \["python", "-m", "bot.main"]`.<br>  * `LABEL org.opencontainers.image.version=\$VERSION\`. | `Dockerfile` |
| **2.2** | **`.dockerignore`**: `__pycache__/`, `tests/`, `docs/`, `.venv/`, `*.log`, `*.db`, `.env`, `.git`.                                                                                                                                                                                                                                                                                                          | `.dockerignore`               |                                                                                                                         |              |
| **2.3** | **Compose конфиги**<br>  `deploy/docker-compose.dev.yml` (build локально) и `docker-compose.prod.yml` (цитирует образ из GHCR).<br>  Общие настройки:<br>  \* volume `./data:/app/data`;<br>  \* `env_file: .env` (prod → `environment:`);<br>  \* `restart: unless-stopped / always`;<br>  \* health-check такой же, как в Dockerfile;<br>  \* порт `8080:8080`.<br>  Ключ `version:` удалён (Compose V2). | `deploy/…`                    |                                                                                                                         |              |
| **2.4** | **Startup-script** `scripts/entrypoint.sh`:<br>`python -m bot.database --init && exec python -m bot.main`.                                                                                                                                                                                                                                                                                                  | `scripts/entrypoint.sh`       |                                                                                                                         |              |
| **2.5** | **Makefile**: цели `docker-build`, `docker-run`, `compose-up`, `compose-down`, `docker-push`.                                                                                                                                                                                                                                                                                                               | `Makefile`                    |                                                                                                                         |              |
| **2.6** | **GitHub Actions — минимальный docker-publish**<br>  \* Новый job `docker-publish` **только** при пуше тегов `v*`.<br>  \* `docker/login-action` → GHCR.<br>  \* `docker/build-push-action` с тегами `${{ github.ref_name }}` и `latest`.<br>  \* **Без** запуска контейнера или compose-integration.                                                                                                       | `.github/workflows/ci.yml`    |                                                                                                                         |              |
| **2.7** | **README & docs**: раздел «Docker / Compose», шаги деплоя, badge GHCR pulls.                                                                                                                                                                                                                                                                                                                                | `README.md`, `docs/deploy.md` |                                                                                                                         |              |
| **2.8** | **pre-commit**: добавить `hadolint` (опционально), но ошибка линта не блокирует CI.                                                                                                                                                                                                                                                                                                                         |                               |                                                                                                                         |              |

---

## 3  I — **Integrate**

| Направление  | Шаги                                                                                                            |
| ------------ | --------------------------------------------------------------------------------------------------------------- |
| Линтеры      | Убедиться, что `Dockerfile`-хук `hadolint` и формат-хук `dockerfilelint` добавлены в `.pre-commit-config.yaml`. |
| CI           | Проверить, что задан `permissions: packages: write` для job `docker-publish` (иначе push в GHCR не пройдёт).    |
| Документация | В `README` добавить quick-start:  `bash\nmake docker-build\nmake docker-run  # localhost:8080/ping\n`           |

---

## 4  P — **Push**

```bash
git add Dockerfile .dockerignore deploy/ scripts/ Makefile \
        tests/conftest.py tests/deploy/*.py .github/workflows/ci.yml \
        README.md docs/deploy.md .pre-commit-config.yaml
git commit -m "build(docker): prod-grade image & compose, skip docker tests on CI, add GHCR publish"
git push origin master
```

---

### ✔️ Ожидаемый результат

| Метрика            | Что видит разработчик / CI                                                                               |
| ------------------ | -------------------------------------------------------------------------------------------------------- |
| **GitHub Actions** | `pytest` ➜ все unit-тесты PASS, docker-метки `skipped`; job `docker-publish` запускается только на теги. |
| **Локально**       | `pytest -m docker` проходит: образ собирается, health-status = healthy, compose-сервис поднимается.      |
| **Образ**          | non-root, лёгкий (≈120 MB), health-check `/ping`, метка версии.                                          |
| **Compose**        | один файл для dev, один для prod; оба томят `./data`, оба проверяют health.                              |
| **Документация**   | чёткие шаги «build → run» и «compose-up».                                                                |

> Теперь и CI зелёный, и полный Docker/Compose-стек готов к одно-кликовому деплою (Railway, Fly.io, VPS).
