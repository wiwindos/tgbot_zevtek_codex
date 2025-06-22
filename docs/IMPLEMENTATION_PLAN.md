### Итерация 4 — **LLM Provider Abstraction (Gemini · Mistral · Dipseek)**

*(T-F-I-P план, привязан к актуальному репо `wiwindos/tgbot_zevtek_codex`)*

---

#### Текущее состояние репозитория (ветка `master`)

| Наблюдение                                                                                                  | Файл / каталог                                             |
| ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Бот-ядро (`/start`, `/ping`) и фабрика `create_bot_and_dispatcher()` реализованы.                           | `bot/main.py`                                              |
| Работают `AuthMiddleware` и (после Iter 3) `ContextMiddleware`, утилита `send_long_message`.                | `bot/middleware.py`, `services/context.py`, `bot/utils.py` |
| Таблицы `users / requests / responses / models` и helper-методы `log_request`, `log_response` присутствуют. | `database.py`                                              |
| Папка **`providers/`** ещё **отсутствует**. В коде прямых вызовов LLM API нет.                              | —                                                          |
| В `tests/` есть проверки `/start`, `/auth`, `/context`, но **нет** тестов для LLM-слоя.                     | `tests/…`                                                  |
| `.env.example` не содержит ключей LLM-провайдеров.                                                          | `.env.example`                                             |

---

## 1. T — **Test first**

| Шаг                                       | Детали                                                                                                                                                                                                                                                                                                                                                            |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Файл**                                  | `tests/providers/test_registry.py`                                                                                                                                                                                                                                                                                                                                |
| **Fixtures**                              | *HTTP-моки* через **`respx`** (для `httpx`), *monkeypatch* для Google Gemini SDK.                                                                                                                                                                                                                                                                                 |
| **Тест-кейс 1 «list\_models агрегирует»** | 1. Создать инстанс `ProviderRegistry()`.<br>2. Замокать `GeminiProvider.list_models` → `[\"gemini-pro\"]`; `MistralProvider.list_models` → `[\"mistral-8x7b\"]`; `DipseekProvider.list_models` → `[\"dipseek-latest\"]`.<br>3. Ожидается, что `await registry.list_all()` вернёт объединённый сет.                                                                |
| **Тест-кейс 2 «generate логирует в БД»**  | 1. Подготовить временную SQLite (та же техника, что в `test_schema.py`).<br>2. Замокать `GeminiProvider.generate` → строка "stub".<br>3. Вызвать high-level функцию `generate_reply(chat_id, prompt, model=\"gemini-pro\")`.<br>4. Проверить, что:<br>• В `requests` появилась запись с нужным `model`; <br>• В `responses` появилась пара с тем же `request_id`. |
| Ожидание                                  | Тесты падают, т.к. нет провайдеров и registry.                                                                                                                                                                                                                                                                                                                    |

---

## 2. F — **Feature**

| №   | Задача                                          | Детали / Файл                                                                                                                                                                                                                           |
| --- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 | **Создать каталог `providers/`**                | ├─ `__init__.py` (реэкспорт Registry)<br>├─ `base.py`<br>├─ `gemini.py`<br>├─ `mistral.py`<br>└─ `dipseek.py`                                                                                                                           |
| 2.2 | **`BaseProvider`**                              | Async-абстракция:<br>`python<br>class BaseProvider(ABC):<br>    name: str  # \"gemini\", \"mistral\"…<br>    async def list_models(self) -> list[str]: ...<br>    async def generate(...): ...<br>    supports_files: bool = False<br>` |
| 2.3 | **`GeminiProvider`**                            | Использовать `google.cloud.aiplatform.gapic.PredictionServiceAsyncClient`.<br>*Методы*:<br>• `list_models()` → парсит Vertex `modelsClient.list_models`.<br>• `generate(prompt, context)` → возвращает текст.                           |
| 2.4 | **`MistralProvider`**                           | HTTP клиент `httpx.AsyncClient`.<br>• `list_models()` GET `/v1/models`.<br>• `generate()` POST `/v1/chat/completions`.                                                                                                                  |
| 2.5 | **`DipseekProvider`**                           | Аналогично Mistral; эндпоинт и ключ берутся из `.env`.                                                                                                                                                                                  |
| 2.6 | **`ProviderRegistry`**                          | Сканирует `BaseProvider` подклассы, инициализирует их с creds из env.<br>Методы:<br>• `list_all()` → объединённый набор;<br>• `get(name)` → провайдер.                                                                                  |
| 2.7 | **High-level helper** `services/llm_service.py` | `python<br>async def generate_reply(chat_id, prompt, model):<br>    req_id = await log_request(... )<br>    text = await provider.generate(... )<br>    await log_response(req_id, text)<br>    return text<br>`                        |
| 2.8 | **Интеграция в бот**                            | В хендлере диалога (будет добавлен позднее) вместо заглушки вызывать `generate_reply`.                                                                                                                                                  |
| 2.9 | **ENV**                                         | Обновить `.env.example`:<br>`\n# Gemini\nGEMINI_PROJECT=\nGEMINI_LOCATION=\nGEMINI_KEY=\n# Mistral\nMISTRAL_API_KEY=\n# Dipseek\nDIPSEEK_ENDPOINT=\nDIPSEEK_API_KEY=\n`                                                                 |

---

## 3. I — **Integrate**

| Действие       | Детали                                                                                                                                                               |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Док-строки** | В каждом провайдере — ссылка на официальную доку, формат payload.                                                                                                    |
| **README**     | Раздел “Supported LLM providers”; таблица `name / supports_files / env_vars`.                                                                                        |
| **pre-commit** | Проверить `providers/*` mypy-strict (ignore\_missing\_imports for external SDK).                                                                                     |
| **CI**         | `requirements.txt` дополнить `google-cloud-aiplatform`, `httpx`, `respx`.<br>Workflow `ci.yml` — `pip install -r requirements.txt` уже есть, тесты сами подхватятся. |

---

## 4. P — **Push**

```bash
git add .
git commit -m "feat(llm): pluggable provider layer (Gemini, Mistral, Dipseek)"
git push origin master
```

---

### Итог итерации 4

| Компонент / Функция            | Состояние                                       |
| ------------------------------ | ----------------------------------------------- |
| Каталог `providers/`           | содержит 3 асинхронных клиента + `BaseProvider` |
| `ProviderRegistry`             | отдаёт список моделей, проксирует генерацию     |
| `services/llm_service.py`      | центровой API для бота + логирование в БД       |
| Тест-набор `tests/providers/*` | зелёный                                         |
| `.env.example`, README         | переменные и инструкция по ключам               |
| CI (lint · tests · docker)     | зелёный                                         |
