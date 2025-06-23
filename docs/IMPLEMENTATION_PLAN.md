### **Новая итерация 9-bis — «Gemini SDK v2 + Proxy & Model Switching»**

*(T – F – I – P чек-лист. Синхронизировано с репо `tgbot_zevtek_codex` на сегодня.)*

---

## Текущее состояние проекта

| Факт                                                                                            | Файл / каталог        |
| ----------------------------------------------------------------------------------------------- | --------------------- |
| Провайдер **`GeminiProvider`** использует Vertex AI (`google-cloud-aiplatform`).                | `providers/gemini.py` |
| Для аутентификации требуются `GEMINI_PROJECT / LOCATION / KEY`.                                 | `.env.example`        |
| Переключение модели доступно через inline-кнопку «Выбрать модель», но список берётся из Vertex. | `bot/model_picker.py` |
| Прокси никак не поддерживаются; конфигурации в БД для «ключ-значение» нет.                      | —                     |
| Таблицы: `users / requests / responses / models / files`.                                       | `database.py`         |

---

## 1. **T — Test first**

| Шаг                                   | Детали                                                                                                                                                                                                                                                                               |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Файл**                              | `tests/providers/test_gemini_proxy.py`                                                                                                                                                                                                                                               |
| **Fixtures**                          | • `monkeypatch.setenv("GEMINI_API_KEY", "dummy")`; <br>• `monkeypatch.setenv("GEMINI_PROXY", "http://191.102.181.223:9653")`; <br>• mock `google.genai._client.genai_internal.Session.request` (capture `proxies`).                                                                  |
| **Тест «proxy applied»**              | Инициализировать `GeminiProvider`, вызвать `generate("hi")` → проверить, что в нижележащем запросе `proxies={"https": "http://191.102…:9653"}`.                                                                                                                                      |
| **Тест «/model switch keeps ctx»**    | 1. Отправить два сообщения (`one`, `two`) на `mistral-8x7b`.<br>2. `/model gemini-pro`.<br>3. Отправить третье (`three`).<br>   • Убедиться, что `GeminiProvider.generate` получает контекст = 3 сообщения.<br>   • База `requests` показывает правильный `model` для каждой записи. |
| **Тест «/admin proxy set … + check»** | 1. `/admin proxy set http://1.1.1.1:8080` → значение сохраняется (см. таблицу `config`).<br>2. `/admin proxy test` вызывает `GeminiProvider.check_proxy()` → при успехе возвращает «OK».                                                                                             |
| Ожидание                              | Упадут: нового SDK, прокси-логики и админ-команд нет.                                                                                                                                                                                                                                |

---

## 2. **F — Feature**

| №       | Задача                                | Файл / модуль                                                                                                                                                                                                                                                                                                                                                                              |
| ------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **2.1** | **Заменить SDK**                      | <br>• Удалить `google-cloud-aiplatform` из `requirements.txt`.<br>• Добавить `google-genai>=0.5` (новый официальный).                                                                                                                                                                                                                                                                      |
| **2.2** | **Новая реализация `GeminiProvider`** | `providers/gemini.py`:<br>`python<br>import google.generativeai as genai<br>genai.configure(api_key=GEMINI_API_KEY, proxy=GEMINI_PROXY)<br>client = genai.GenerativeModel(DEFAULT_MODEL)<br>`<br>• Метод `generate()` — sync SDK → обернуть `run_in_threadpool` для async.<br>• Метод `list_models()` → `genai.list_models()` с фильтром `'generation' in m.supported_generation_methods`. |
| **2.3** | **Proxy поддержка**                   | <br>• Чтение `GEMINI_PROXY` из `.env`.<br>• Класс-конфиг `Settings` в `providers/__init__.py` хранит текущее значение (из БД или env).<br>• Вызов `genai.configure(proxy=…)` при изменении.                                                                                                                                                                                                |
| **2.4** | **Глобальная таблица `config`**       | `database.py`:<br>`CREATE TABLE IF NOT EXISTS config ( key TEXT PRIMARY KEY, value TEXT );`<br>Helpers: `get_config(key, default) / set_config(key, value)`.                                                                                                                                                                                                                               |
| **2.5** | **Админ-команды «proxy»**             | В `bot/admin_proxy.py`:<br>• `/admin proxy set <string>` → `set_config("GEMINI_PROXY", value)` + перезвон `GeminiProvider.reload_settings()`.<br>• `/admin proxy test` → вызывает `GeminiProvider.check_proxy()` (pings `https://api.ipify.org`).                                                                                                                                          |
| **2.6** | **Выбор модели через команду**        | Новый public-хендлер `/model <name>`:<br>• Валидирует, что `<name>` есть в `models`.<br>• Сохраняет выбор в контексте (in-memory dict `chat_id → current_model`).<br>• Ответ «Модель переключена на …».                                                                                                                                                                                    |
| **2.7** | **Контекст сквозь модели**            | `ContextBuffer` уже хранит историю; `generate_reply(chat_id, prompt, model)` теперь берёт `context_buffer.get(chat_id)` без фильтра по модели, т.е. переподключение модели никак не чистит очередь.                                                                                                                                                                                        |
| **2.8** | **ENV-шаблон**                        | Обновить `.env.example`:<br>`\n# Gemini via GenAISDK\nGEMINI_API_KEY=\nGEMINI_PROXY=\nDEFAULT_MODEL=gemini-pro\n`                                                                                                                                                                                                                                                                          |
| **2.9** | **Док-строки и проверки**             | • `GeminiProvider.check_proxy()` делает HEAD `https://www.google.com/generate_204` через proxy; кидает `ProxyError` → ловим в `/admin proxy test`.                                                                                                                                                                                                                                         |

---

## 3. **I — Integrate**

| Действие             | Описание                                                                                                                                         |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **README**           | Новый раздел “Gemini via GenAISDK + Proxy”: как получить API-ключ в AI Studio, пример `proxy set` / `proxy test`, список поддерживаемых моделей. |
| **Tests & CI**       | Добавить `google-genai` в `requirements.txt`; тест `test_gemini_proxy.py` подключить к CI.                                                       |
| **pre-commit**       | Mypy stubs: `types-google-genai` (или `ignore_missing_imports = True`).                                                                          |
| **Migration script** | При старте (`init_db()`): если таблицы `config` нет → создать.                                                                                   |

---

## 4. **P — Push**

```bash
git add .
git commit -m "feat(gemini): migrate to google-genai SDK with proxy support and runtime model switch"
git push origin master
```

---

### Результат итерации 8-bis

| Компонент / Функция                 | Состояние                                          |
| ----------------------------------- | -------------------------------------------------- |
| **GeminiProvider**                  | использует `google-genai`, async-friendly          |
| **Прокси**                          | задаётся через env/админ-команду, health-чек       |
| **Таблица `config`**                | хранит глобальные KV (GEMINI\_PROXY, …)            |
| **Команда `/model <name>`**         | мгновенно переключает модель, контекст сохраняется |
| **Команды `/admin proxy set/test`** | управление прокси без перезапуска                  |
| **Тесты**                           | покрывают proxy-инжекцию и model-switch            |
| **Документация + env**              | обновлены                                          |
| **CI**                              | зелёный                                            |

