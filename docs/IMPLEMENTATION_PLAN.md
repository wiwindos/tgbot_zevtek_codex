### Итерация 1 — Database Schema with **aiosqlite**

> **Текущее состояние репо**
>
> * В `database.py` уже есть `init_db()` и одна таблица `users` (только id, tg\_id, name) .
> * В зависимостях уже присутствует **aiosqlite** .
> * Тестов и вспомогательных функций для работы с БД пока нет.

Наша цель — полноценная схема (`users`, `requests`, `responses`, `models`) + базовый слой доступа и покрытие юнит-тестами.

---

#### 1. **T — Test first**

1. **Создать каталог `tests/db/`** и файл `test_schema.py`.
2. В тесте:

   * C помощью `tempfile.TemporaryDirectory()` подменить `DB_PATH` на временный файл (через `monkeypatch`).
   * Вызвать `await init_db()` — ожидание, что все 4 таблицы существуют:

     ```sql
     PRAGMA table_info(users);
     PRAGMA foreign_key_list(responses);
     ```
   * Проверить ключевые колонки (`user_id`, `request_id`, `provider`, `updated_at`) и внешние ключи:

     * `requests.user_id → users.id`
     * `responses.request_id → requests.id`
   * Попробовать вставить демо-данные и убедиться, что каскадные ограничения работают (например, попытка ответа на несуществующий `request_id` должна падать).
3. Запустить `pytest -q` — тест, конечно, упадёт (таблиц нет).

---

#### 2. **F — Feature**

1. **Расширить `database.py`**:

   * Добавить SQL-константы `CREATE_REQUESTS`, `CREATE_RESPONSES`, `CREATE_MODELS`.
   * В `init_db()` выполнить их в транзакции.
   * Включить `PRAGMA foreign_keys=ON` сразу после подключения.
2. **Асинхронный слой доступа** (минимально):

   * `async def get_db()` — контекст-менеджер, возвращающий соединение.
   * `async def log_request(user_id, prompt, model)` → возвращает `request_id`.
   * `async def log_response(request_id, content)`.
   * Эти функции пока не используются ботом, но нужны для следующих итераций и тестов.
3. (Не писать сейчас) добавить место-заглушку под «миграции» (будущее расширение).
4. Прогнать `pytest` — должно стать зелёным.

---

#### 3. **I — Integrate**

1. **Документация схемы**:

   * В начале `database.py` поместить ASCII-ERD или markdown-блок с описанием таблиц/связей.
   * Обновить `README` раздел «Database» (как инициализируется, где лежит файл, как включить PRAGMA foreign\_keys).
2. **pre-commit**:

   * Добавить `sqlfmt` (или `pg_format` Wrapper) в `.pre-commit-config.yaml` для автоформатирования \*.sql блоков в исходниках (необязательно, но полезно).
3. **CI (`ci.yml`)**:

   * В блоке `jobs.test.steps` после установки зависимостей добавить `pytest -q tests/db`.
   * Убедиться, что логи CI не публикуют чувствительных данных (.env у нас тестовый).

---

#### 4. **P — Push**

1. Коммит:

   ```
   feat(db): introduce full sqlite schema and tests
   ```
2. Pull-request → убедиться, что:

   * **Lint** зелёный,
   * **Tests** зелёные,
   * **Docker dry-run** всё ещё собирается.

---

#### Результат итерации

| Компонент                                       | Состояние после Iter 1                  |
| ----------------------------------------------- | --------------------------------------- |
| Таблицы `users / requests / responses / models` | созданы & проверены                     |
| `init_db()`                                     | включает все DDL + PRAGMA FK            |
| Асинхр. helper-методы                           | `get_db`, `log_request`, `log_response` |
| Юнит-тесты                                      | `tests/db/test_schema.py` зелёные       |
| CI                                              | тестирует схему                         |
