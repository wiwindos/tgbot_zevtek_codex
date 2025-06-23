# GENERAL\_IMPLEMENTATION\_PLAN.md

> **Methodology:** Each iteration follows a strict T‑F‑I‑P cycle — **T**est‑driven skeleton, **F**eature implementation, **I**ntegration (refactor + docs), **P**ush.  All code is committed with conventional‑commits style messages.  All tests use `pytest‑asyncio` with extensive fixtures and mocks.

---

## Iteration 0 — Project Bootstrap & CI Skeleton

| Phase              | Tasks                                                                                                                                                                                                                                                                                   |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **T (Test first)** | *`tests/test_smoke.py`* — expect bot to launch and reply "Bot ready" to `/ping` (failing).                                                                                                                                                                                              |
| **F (Feature)**    | 1. Create poetry project / update `requirements.txt`.<br>2. Add `bot/__init__.py` + minimalist `main.py` with `/ping` handler using **aiogram**.<br>3. Add `.env.example` & load via `python‑dotenv`.<br>4. Implement CLI `python -m bot --ping` returning 0.<br>5. Ensure test passes. |
| **I (Integrate)**  | 1. Add pre‑commit (black, isort, flake8, mypy stubbed).<br>2. Configure **GitHub Actions** workflow: `lint`, `test`, `docker‑build` (dry‑run).                                                                                                                                          |
| **P (Push)**       | `feat(core): bootstrap project with ping command`                                                                                                                                                                                                                                       |

---

## Iteration 1 — Database Schema with **aiosqlite**

| Phase | Tasks                                                                                                                                              |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **T** | *`tests/db/test_schema.py`* — `init_db()` creates tables & foreign keys; inserting sample row succeeds.                                            |
| **F** | 1. `db/models.sql` — idempotent DDL.<br>2. `db/__init__.py` with `init_db(path:str)`, `get_db()` (async context).<br>3. Script auto‑runs on start. |
| **I** | Docstring diagrams using **erd‑antic** comment blocks.<br>Update README with schema table description.                                             |
| **P** | `feat(db): initial aiosqlite schema and helpers`                                                                                                   |

---

## Iteration 2 — Authorization Flow

| Phase | Tasks                                                                                                                                                                             |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **T** | *`tests/bot/test_auth.py`* — unauthorized user receives request‑pending msg; admin approval flips `is_active`, subsequent message allowed. Mock TG API with `aiogram-testing`.    |
| **F** | 1. Add middleware `AuthMiddleware` reading `users` table.<br>2. `/start` registers request, notifies admin group id from `.env`.<br>3. `/admin approve <user_id>` activates user. |
| **I** | Factor out `services/user_service.py`.<br>Emoji‑based confirmation messages.                                                                                                      |
| **P** | `feat(auth): interactive approval workflow inside bot`                                                                                                                            |

---

## Iteration 3 — Context Buffer & Message Splitting

| Phase | Tasks                                                                                                                                       |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **T** | *`tests/bot/test_context.py`* — after 3 conversational turns history length == 3; `/clear` empties context. Long (>4096) response is split. |
| **F** | 1. Implement per‑chat circular buffer in `services/context.py` (configurable max\_tokens).<br>2. Utility `send_long_message()` chunker.     |
| **I** | Add `/clear` command help.<br>Refactor tests.                                                                                               |
| **P** | `feat(conversation): context retention & safe split`                                                                                        |

---

## Iteration 4 — LLM Provider Abstraction (Gemini, Mistral, Dipseek)

| Phase | Tasks                                                                                                                                                                                                                                      |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **T** | *`tests/providers/test_registry.py`* — registry returns provider, mocks call, stores request/response in DB.                                                                                                                               |
| **F** | 1. `providers/base.py` proto‑class with `list_models()` & `generate()`.<br>2. `gemini.py` uses `google-cloud-aiplatform` async.<br>3. `mistral.py` httpx client.<br>4. `dipseek.py` httpx client.<br>5. `ProviderRegistry` auto‑discovers. |
| **I** | Inject provider via inline‑keyboard; store chosen model in context.                                                                                                                                                                        |
| **P** | `feat(llm): pluggable provider layer`                                                                                                                                                                                                      |

---

## Iteration 5 — Scheduler for Model Auto‑Refresh

| Phase | Tasks                                                                                                                                                                     |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **T** | *`tests/scheduler/test_refresh.py`* — advance fake timer; models table updated; admin notified.                                                                           |
| **F** | 1. Integrate **APScheduler** inside `scheduler/__init__.py`.<br>2. Daily job runs `pull_and_sync_models()` across providers.<br>3. Diff detection → `bot_notify_admin()`. |
| **I** | Config param `REFRESH_CRON` in `.env`.                                                                                                                                    |
| **P** | `feat(scheduler): daily model sync & notify`                                                                                                                              |

---

## Iteration 6 — File Handling (if provider supports)

| Phase | Tasks                                                                                                                                    |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **T** | *`tests/bot/test_file.py`* — upload PDF, provider stub returns summary. Response stored & file path logged.                              |
| **F** | 1. `file_service.py` saves to `/data/files/` with uuid.<br>2. Detect file message, pass path/bytes to provider if `supports_files=True`. |
| **I** | Update DB: add `files` table (request\_id, path, mime).                                                                                  |
| **P** | `feat(files): accept & relay user files`                                                                                                 |

---

## Iteration 7 — Admin Command Suite Enhancement

| Phase | Tasks                                                                                                                 |
| ----- | --------------------------------------------------------------------------------------------------------------------- |
| **T** | *`tests/bot/test_admin_cmds.py`* — `/admin stats` returns counts; `/admin users pending` lists requests.              |
| **F** | 1. Expand admin router: stats, list models, manual refresh, toggle user.<br>2. Password validation flow with timeout. |
| **I** | Markdown doc `docs/admin_commands.md`.                                                                                |
| **P** | `feat(admin): extended in‑bot management`                                                                             |

---

## Iteration 8 — Observability & Error Handling

| Phase | Tasks                                                                                                       |
| ----- | ----------------------------------------------------------------------------------------------------------- |
| **T** | *`tests/integration/test_errors.py`* — simulate provider 500; user gets graceful message; error logged.     |
| **F** | 1. Add `structlog` JSON logger shipped to stdout.<br>2. Global exception middleware sending trace to admin. |
| **I** | Configure GitHub Actions to save artifacts / coverage.                                                      |
| **P** | `chore(obs): structured logging & Sentry hooks`                                                             |

---

## Iteration 9 — Docker, Compose & One‑Click Deploy

| Phase | Tasks                                                                                                                                               |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **T** | (docker image test удалён из-за отсутствия Docker) |
| **F** | 1. Write `Dockerfile` (python slim, non‑root).<br>2. `docker‑compose.yml` with named volume for `sqlite`.<br>3. Add CI stage to push image to GHCR. |
| **I** | Update README deployment section.                                                                                                                   |
| **P** | `ci(docker): automated image build & push`                                                                                                          |

---

## Iteration 10 — Polish & Documentation Finish

| Phase | Tasks                                                                                                                                    |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **T** | *`tests/docs/test_readme_links.py`* — all docs internal links resolve (markdown‑link‑check).                                             |
| **F** | 1. Complete `CONTEXT.md` with business goals.<br>2. Write change‑log, license, code‑of‑conduct.<br>3. Make `make lint` composite target. |
| **I** | Final code formatting pass, bump version to 1.0.0.                                                                                       |
| **P** | `docs: project ready for prime time 🎉`                                                                                                  |
