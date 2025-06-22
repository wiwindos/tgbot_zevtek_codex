### Итерация 6 — **File Handling (upload → LLM → reply)**

*(чет-пошаговый T – F – I – P план; состояние синхронизировано с репозиторием `wiwindos/tgbot_zevtek_codex`)*

---

#### Текущее состояние (`master`)

| Факт                                                                                                                                   | Файл / каталог            |
| -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| Базовый бот с `/start`, `/ping`, `/clear`; `AuthMiddleware`, `ContextMiddleware`, сплиттер длинных сообщений.                          | `bot/…`                   |
| Провайдеры `GeminiProvider`, `MistralProvider`, `DipseekProvider`; у класса `BaseProvider` флаг `supports_files = False` по-умолчанию. | `providers/…`             |
| Сервис `generate_reply()` логирует запрос/ответ в таблицы `requests` и `responses`.                                                    | `services/llm_service.py` |
| Таблица `files` **не существует**, приём вложений TG не обрабатывается.                                                                | —                         |
| Scheduler (Iter 5) обновляет `models` и шлёт уведомления админу.                                                                       | `scheduler/jobs.py`       |
| В `tests/` отсутствуют проверки файлового пути.                                                                                        | `tests/…`                 |

---

## 1. **T — Test first**

| Шаг                                      | Детали                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Файл**                                 | `tests/bot/test_file.py`                                                                                                                                                                                                                                                                                                              |
| **Fixtures**                             | • tmpdir + `init_db()`; <br>• мок `GeminiProvider.supports_files = True` и `GeminiProvider.generate` (ожидает bytes).                                                                                                                                                                                                                 |
| **Тест-кейс 1 «upload + summary»**       | 1. Через фикстуру создаём `Message` с типом `document` (`file_id="123", file_name="demo.pdf"`).<br>2. Middleware/handler вызывает приём, сохраняет файл в `/data/files/<uuid>.pdf`.<br>3. Проверяем:<br>• таблица `files` получила запись (`path`, `mime`, `request_id`);<br>• `GeminiProvider.generate` был вызван (переданы bytes). |
| **Тест-кейс 2 «provider без поддержки»** | Подменяем `MistralProvider.supports_files = False`.<br>Отправляем файл + выбранная модель `mistral-*` → бот отвечает «Эта модель не принимает файлы», `GeminiProvider.generate` не вызывается.                                                                                                                                        |
| Ожидание                                 | Тесты падают — ни таблицы, ни логики нет.                                                                                                                                                                                                                                                                                             |

---

## 2. **F — Feature**

| №   | Задача                                          | Файл / модуль                                                                                                                                                                                                                                                                                                                                                                                                         |                                                                                                                                       |
| --- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 | **Добавить таблицу `files`**                    | В `database.py`:<br>`sql<br>CREATE TABLE IF NOT EXISTS files ( id INTEGER PK, request_id INTEGER, path TEXT, mime TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(request_id) REFERENCES requests(id) ON DELETE CASCADE);`                                                                                                                                                                         |                                                                                                                                       |
| 2.2 | **Helper-метод**                                | `async def log_file(request_id, path, mime)` — insert в `files`.                                                                                                                                                                                                                                                                                                                                                      |                                                                                                                                       |
| 2.3 | **Хранилище файлов**                            | Каталог `/data/files` (создавать при старте, if not exists).                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                       |
| 2.4 | **Handler «file\_message»**                     | Новый роутер `bot/file_handlers.py`:<br>1. Принимает `Document`/`Photo`/`Audio`.<br>2. Скачивает файл: `await bot.get_file`, затем `await bot.download_file(file_path, dest)`. (Использовать `aiofiles` + `Bot.download_file` async).<br>3. Вызывает `generate_reply(chat_id, prompt='', model=selected, file_bytes=bytes)` **если** `provider.supports_files`.<br>4. Иначе отправляет «Модель … не принимает файлы». |                                                                                                                                       |
| 2.5 | **Расширить `BaseProvider.generate` сигнатуру** | \`def generate(prompt, context, file\_bytes: bytes                                                                                                                                                                                                                                                                                                                                                                    | None = None)`. Провайдеры, где `supports\_files=False`, должны игнорировать `file\_bytes`и кидать`NotImplementedError`если не`None\`. |
| 2.6 | **Реализация в GeminiProvider**                 | Если передан `file_bytes`, строит `Part(content=file_bytes, mime_type=mime)` и кладёт в `contents`, режим «multimodal».                                                                                                                                                                                                                                                                                               |                                                                                                                                       |
| 2.7 | **Вызов `log_file`**                            | После получения `request_id` в `generate_reply()` — если файл присутствует, сохраняет запись.                                                                                                                                                                                                                                                                                                                         |                                                                                                                                       |
| 2.8 | **.env**                                        | Путь хранения можно настраивать: `FILES_DIR=./data/files`.                                                                                                                                                                                                                                                                                                                                                            |                                                                                                                                       |
| 2.9 | **Отправка ответа**                             | Использовать уже существующий `send_long_message` для текстового ответа, плюс, если провайдер вернёт файл (пока не нужно).                                                                                                                                                                                                                                                                                            |                                                                                                                                       |

---

## 3. **I — Integrate**

| Действие       | Детали                                                                                                  |
| -------------- | ------------------------------------------------------------------------------------------------------- |
| **README**     | Новый раздел «Работа с файлами»: список поддерживаемых расширений и моделей.                            |
| **pre-commit** | Проверка mypy на `bot/file_handlers.py`.                                                                |
| **CI**         | `requirements.txt` — возможно добавить `aiofiles`. Тесты в `tests/bot/test_file.py` теперь исполняются. |
| **Док-строки** | В `BaseProvider.generate` описать параметр `file_bytes`.                                                |

---

## 4. **P — Push**

```bash
git add .
git commit -m "feat(files): accept TG documents, persist to DB and pass to file-capable LLMs"
git push origin master
```

---

### Итог Iter 6

| Компонент / Функция            | Состояние                                     |
| ------------------------------ | --------------------------------------------- |
| Таблица `files`                | создана, каскад `request_id`                  |
| `bot/file_handlers.py`         | скачивает вложения, вызывает LLM              |
| Расширение `BaseProvider`      | сигнатура `file_bytes`, флаг `supports_files` |
| Поддержка в `GeminiProvider`   | multi-modal запрос                            |
| `log_file()` + физ. папка      | реализованы                                   |
| Тесты `tests/bot/test_file.py` | зелёные                                       |
| README / .env                  | обновлены                                     |
| CI / pre-commit                | проходит                                      |
