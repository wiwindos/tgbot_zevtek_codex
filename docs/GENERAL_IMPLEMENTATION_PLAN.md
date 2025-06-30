Below — расширение дорожной карты, продолжающее исходные 0-10 итерации.
Формат и методология T-F-I-P те же, чтобы план «пришился» к уже существующему GENERAL\_IMPLEMENTATION\_PLAN.md.

```markdown
# GENERAL_IMPLEMENTATION_PLAN.md  ← v1.1 (дополнение)

> **Methodology recap:** Every iteration keeps the T-F-I-P loop  
> **T**est-driven-first → **F**eature code → **I**ntegration (refactor + docs) → **P**ush with conventional-commits.  
> New tests rely on `pytest-asyncio`, `aiogram-testing`, `pytest-httpx`.  
> Doc changes go to README, CONTEXT.md, docs/*.md **в одном и том же PR**.

---

## Iteration 11 — Documentation Sync & Deepseek Rename

| Phase | Tasks |
| ----- | ----- |
| **T** | *`tests/docs/test_plan_state.py`* — проверка, что README содержит «Deepseek», а строк «dipseek» нет (фейл до правок). |
| **F** | 1. Переименовать все «dipseek» → «deepseek» в коде, env-vars, миграции **(src, tests, docs)**.<br>2. Миграция БД: `UPDATE models SET provider='deepseek' WHERE provider='dipseek';`. |
| **I** | - README, AGENTS.md, docs/admin\_commands.md — убрать старые упоминания прокси, обновить секцию провайдеров.<br>- Добавить changelog флаг **Breaking Change**. |
| **P** | `refactor(core): rename dipseek→deepseek & sync docs` |

---

## Iteration 12 — Provider Picker & Inline Model Selector

| Phase | Tasks |
| ----- | ----- |
| **T** | *`tests/bot/test_provider_switch.py`* —<br>1) `/providers` → выбрать Mistral; `/models` выводит только модели Mistral.<br>2) Переключение модели не меняет provider.<br>3) Возврат к старому provider восстанавливает раннюю модель. |
| **F** | 1. Новый хэндлер `/providers` → inline-кнопки `provider_cb:<name>`.<br>2. `/models` фильтрует модели выбранного провайдера; callback `model_cb:<name>` сохраняет модель.<br>3. Расширить `ContextStorage`: `per_user_provider`, `per_user_model[provider]`.<br>4. Обновить Gemini/Mistral/Deepseek providers: `set_model()`.<br>5. Registry auto-inject выбранную модель в запрос. |
| **I** | - HELP_TEXT распространяет новые команды.<br>- Добавить ER -диаграмму провайдер↔модель в CONTEXT.md. |
| **P** | `feat(ui): /providers & inline model picker` |

---

## Iteration 13 — Gemini Multimodal File Pipeline

| Phase | Tasks |
| ----- | ----- |
| **T** | *`tests/bot/test_file_gemini.py`* —<br>a) Отправка PNG → модель отвечает «(image received)» (mock).<br>b) PDF > 512 kB → бот сообщает «файл слишком велик». |
| **F** | 1. `file_service.detect_mime()` + size guard.<br>2. `GeminiProvider.generate()` — медиапарт из bytes → Base64 (или helper `genai.upload_multipart`).<br>3. Расширить `supports_files` флагами per-mime (image, audio, text). |
| **I** | README → таблица поддерживаемых форматов.<br>docs/file_handling.md — примеры. |
| **P** | `feat(gemini): multimodal image|audio support` |

---

## Iteration 14 — Graceful Error Handling & Model Fallback

| Phase | Tasks |
| ----- | ----- |
| **T** | *`tests/integration/test_fallback.py`* — мок провайдера бросает `httpx.TimeoutException`; бот отвечает «Модель недоступна, выберите /models». |
| **F** | 1. Wrapper `safe_generate()` в `services/llm.py` с try/except.<br>2. Автоматическое предложение inline-кнопки «📋 /Models».<br>3. Global `ErrorMiddleware` → log JSON через structlog. |
| **I** | Добавить Sentry DSN переменную в .env.example, описать включение. |
| **P** | `feat(ux): graceful provider errors with hint` |

---

## Iteration 15 — Context-Limit Notifier (>1000 chars)

| Phase | Tasks |
| ----- | ----- |
| **T** | *`tests/bot/test_context_limit.py`* — после достижения 1100 символов бот отправляет предупреждение, повторно не спамит до очистки. |
| **F** | 1. В `context.py` хранить `warned`-флаг per chat.<br>2. Проверка сумм. len контекста после добавления нового сообщения.<br>3. Команда `/new` (alias `/clear`) — сброс флага. |
| **I** | README: секция «Контекст и лимиты». |
| **P** | `feat(ctx): auto-remind to /new when history>1000` |

---

## Iteration 16 — Proxy Decommission & Config Cleanup

| Phase | Tasks |
| ----- | ----- |
| **T** | *`tests/config/test_no_proxy.py`* — `.env` без `GEMINI_PROXY`; бот стартует; команда `/admin proxy …` отсутствует в `/help`. |
| **F** | 1. Удалить `admin_proxy.py`, env `GEMINI_PROXY`, колонки `proxy_url`.<br>2. Maven-style Alembic migration: drop column. |
| **I** | Чистка README, docs/admin\_commands.md.<br>Секция «Docker proxy» (общесистемно). |
| **P** | `refactor(cfg): remove gemini proxy support` |

---

## Iteration 17 — Command Suite Finalisation

| Phase | Tasks |
| ----- | ----- |
| **T** | *`tests/bot/test_commands.py`* — `/start`, `/help`, `/context`, `/new`, `/providers`, `/models` все отвечают и не превышают 4096 симв. |
| **F** | 1. Дописать `/context` хэндлер (safe split).<br>2. `/start` расширить описанием возможностей.<br>3. `/help` обновить, удалить proxy-раздел. |
| **I** | Зеркальное изменение English README (если есть). |
| **P** | `feat(cmd): full public command palette` |

---

## Iteration 18 — Regression Suite & Coverage >85 %

| Phase | Tasks |
| ----- | ----- |
| **T** | Развернуть `pytest-cov`; GH Action «coverage» fails <85 %. |
| **F** | 1. Дописать missing path tests (edge cases).<br>2. Upload `coverage.xml` as artifact.<br>3. Badge in README. |
| **I** | Настроить Codecov или GH-native coverage summary. |
| **P** | `ci(test): enforce 85% coverage gate` |

---

### Release Tagging

* После Iteration 18 — **tag v1.1.0**  
* Changelog entries grouped under **Added**, **Changed**, **Removed**, **Fixed** — semver-strict.

---

*Документ дополняет предыдущие итерации 0-10 и закрывает все задачи, перечисленные в вашем последнем требовании.*
```
