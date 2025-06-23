### **Новая итерация 8-bis — Proxy Gateway & Model Selector**

*(добавлена между Iter 8 и Iter 9 в **GENERAL\_IMPLEMENTATION\_PLAN.md**; план в формате T – F – I – P)*

---

#### Текущее состояние репозитория (после Iter 8)

| Факт                                                                                                       | Файл / каталог           |
| ---------------------------------------------------------------------------------------------------------- | ------------------------ |
| **GeminiProvider** обращается к Vertex AI напрямую через `google-cloud-aiplatform`, параметров прокси нет. | `providers/gemini.py`    |
| У пользователей есть inline-кнопка выбора модели, но смена сохраняется только на один запрос.              | `bot/handlers/dialog.py` |
| Контекст-буфер работает, хранит цепочку для каждого чата.                                                  | `services/context.py`    |
| Админ-router уже существует (approve, stats и т. д.).                                                      | `bot/admin_router.py`    |

---

## 1. **T — Test first**

| № | Тест-кейс                           | Проверка                                                                                                                                                                   |
| - | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | **`/admin proxy set <str>`**        | • Из админ-чата отправляем строку `191.102.181.223:9653:F8AaEo:rFkG`.<br>• Бот отвечает «Proxy saved ✅».<br>• В БД таблица `settings` содержит key=`gemini_proxy`.         |
| 2 | **`/admin proxy check`**            | • Мокаем `httpx.AsyncClient.get` → OK.<br>• Бот отвечает «Proxy alive 🟢 (120 ms)».                                                                                        |
| 3 | **Смена модели юзером**             | • Пользователь `/model mistral-8x7b`.<br>• Буфер `ContextBuffer.get(chat_id)` всё ещё хранит предыдущие сообщения (len > 0).<br>• Следующий ввод уходит в MistralProvider. |
| 4 | **Gemini запрос идёт через прокси** | • Ставим прокси в таблице.<br>• Мокаем `httpx.AsyncClient.post` и убеждаемся, что вызывает `proxies={"all://": "..."} `.                                                   |

Все тесты сейчас падают.

---

## 2. **F — Feature**

| №   | Задача                         | Файл / модуль                                                                                                                                                                                                             |
| --- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 | **Таблица `settings`**         | В `database.py`: `CREATE TABLE IF NOT EXISTS settings (key TEXT PK, value TEXT)`; helpers `get_setting`, `set_setting`.                                                                                                   |
| 2.2 | **Proxy-Aware GeminiProvider** | • Доп. поле `_proxy_url`.<br>• Конструктор читает `get_setting("gemini_proxy")`.<br>• При `generate()` создаёт `httpx.AsyncClient(proxies={"all://": self._proxy_url})` если указано.                                     |
| 2.3 | **Admin-команды**              | *В `admin_router`*:  <br>• `/admin proxy set <str>` — валидация, запись в `settings`, reply OK.<br>• `/admin proxy check` — HEAD-запрос к `https://generativelanguage.googleapis.com` через текущий прокси; измеряем RTT. |
| 2.4 | **Хранение выбранной модели**  | • В `services/context.py` добавить `selected_model` внутри per-chat state.<br>• Команда `/model <name>` (или inline список) записывает новое значение, **не** обнуляя `history`.                                          |
| 2.5 | **Команда `/models`**          | Показывает список `ProviderRegistry.list_all()` для пользователя.                                                                                                                                                         |
| 2.6 | **Маршрутизация запроса**      | В `generate_reply(chat_id, prompt)` получать `model=context.selected_model` либо default `os.getenv("DEFAULT_MODEL")`.                                                                                                    |
| 2.7 | **ENV / defaults**             | `.env.example` — `DEFAULT_MODEL=gemini-pro`, `GEMINI_PROXY=`.                                                                                                                                                             |

---

## 3. **I — Integrate**

| Задача         | Детали                                                                             |
| -------------- | ---------------------------------------------------------------------------------- |
| **README**     | Новый подраздел “Proxy for Gemini” с форматом `host:port:user:pass`.               |
| **Docs**       | Обновить `docs/admin_commands.md` описанием `/admin proxy*`.                       |
| **pre-commit** | mypy-strict для `providers/gemini.py`, `bot/admin_router.py`.                      |
| **CI**         | В тестовом контейнере установить `httpx[socks]` (для прокси-URL типа `socks5://`). |

---

## 4. **P — Push**

```bash
git add .
git commit -m "feat(proxy): per-admin Gemini proxy config + persistent model selector"
git push origin master
```

---

### **Результат итерации 8-bis**

| Компонент / Функция                   | Статус                               |
| ------------------------------------- | ------------------------------------ |
| Таблица `settings`                    | хранит `gemini_proxy`                |
| Команды `/admin proxy set / check`    | работают, проверяют RTT              |
| Переключатель `/model`                | сохраняет выбор, история не теряется |
| GeminiProvider                        | использует прокси из БД              |
| Тест-набор `test_proxy`, `test_model` | зелёный                              |
| README / docs                         | обновлены                            |
| CI                                    | проходит                             |
