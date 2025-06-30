### Итерация 14 — **Graceful Error Handling & Model Fallback**

> **Исходное состояние после Iter 13**
>
> * Запросы к LLM-API могут завершаться тайм-аутами или 4xx/5xx. Сейчас исключения ловит `ErrorMiddleware`, но:
>   – пользователь не получает понятного уведомления;
>   – нет подсказки «выбери другую модель»;
>   – ошибки не агрегируются для быстрой диагностики.
> * Логи пишутся через `structlog`, формат сообщений не унифицирован.

**Цель итерации — мягкая обработка сбоев провайдера:**

1. Унифицированно перехватывать ВСЕ ошибки генерации.
2. Отправлять пользователю дружелюбное сообщение + inline-кнопку «📋 Модели».
3. Логировать ошибку в структуре и дать администратору on-demand команду `/admin errors`--сводка топ-ошибок за последние 24 ч.

---

#### 1. **T — Test first**

`tests/integration/test_fallback.py`

| Сценарий                | Ожидаемое поведение                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A: сбой провайдера**  | 1) Мокаем `GeminiProvider.generate` → `httpx.TimeoutException`. 2) Пользователь пишет «Привет». 3) Бот отвечает:<br>`⚠️ Не удалось получить ответ от модели gemini-pro. Попробуйте выбрать другую модель.`<br>+ inline-кнопка «📋 Модели». 4) В `caplog` есть запись `provider_error` c полями `provider="gemini"`, `model="gemini-pro"`, `error="TimeoutException"`. 5) Контекст содержит **только** пользовательское сообщение. |
| **B: смена модели**     | Нажимаем «📋 Модели», выбираем `deepseek-base` (мок-ответ «ok») → бот успешно отвечает.                                                                                                                                                                                                                                                                                                                                           |
| **C: админская сводка** | Мокаем 3 разных ошибки, затем админ пишет `/admin errors`.<br> Бот отправляет таблицу вида:<br>`Gemini gemini-pro TimeoutException ×2`<br>`Mistral mistral-small HTTPStatusError ×1`                                                                                                                                                                                                                                              |

Все тесты красные до реализации.

---

#### 2. **F — Feature**

1. **`safe_generate()` + `ProviderError`**

   ```python
   class ProviderError(Exception):
       def __init__(self, provider, model, exc, elapsed):
           self.provider, self.model = provider, model
           self.orig_exc, self.elapsed = exc, elapsed
   async def safe_generate(provider, prompt, files=None):
       start = perf_counter()
       try:
           return await provider.generate(prompt, files=files)
       except Exception as exc:
           raise ProviderError(provider.name, provider.model, exc, perf_counter()-start)
   ```
2. **Хэндлер ошибок** (`conversation.py`)

   * Оборачиваем вызов `safe_generate`.
   * При `ProviderError` →

     * лог (`logger.warning("provider_error", …)`),
     * ответ пользователю (`send_long_message(..., log=False)`) с кнопкой

       ```python
       kb = InlineKeyboardMarkup(inline_keyboard=[[
           InlineKeyboardButton(text="📋 Модели", callback_data="show_models")
       ]])
       ```
   * Контекст не пополняем ответом-ошибкой.
3. **Callback `show_models`**

   * Переиспользует логику `/models`.
   * Ответ — редактирует реплай или шлёт новое сообщение со списком моделей.
4. **Хранилище ошибок**

   * Таблица `errors(id, provider, model, error, created_at)` (SQLite).
   * При `provider_error` → `INSERT`.
   * Вставка выполняется через новый сервис `error_service.py`.
5. **Админ-команда `/admin errors`**

   * SQL-запрос: сводка за последние 24 ч.

     ```sql
     SELECT provider, model, error, COUNT(*) n
     FROM errors
     WHERE created_at >= DATETIME('now','-1 day')
     GROUP BY provider, model, error
     ORDER BY n DESC;
     ```
   * Форматируем Markdown-таблицу; если записей нет — «Ошибок за последние 24 ч нет».
   * Роутер доступен только `ADMIN_CHAT_ID`.
6. **Структурный лог**

   * Поля: `provider, model, error, elapsed_ms, user_id, msg="provider_error"`.
   * Уровень `warning`, вывод в stdout (подхватывает Docker-лог).

---

#### 3. **I — Integrate**

| Задача           | Действия                                                                                                                                                    |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Документация** | *README* — раздел «🚑 Ошибки и fallback»: пример сообщения + описание `/admin errors`.<br>*docs/admin\_commands.md* — добавить раздел «Ошибки провайдеров». |
| **CHANGELOG**    | **Added** — graceful error UI; `/admin errors` summary.<br>**Changed** — все вызовы LLM через `safe_generate`.                                              |
| **БД миграция**  | `scripts/migrate.py` — `CREATE TABLE IF NOT EXISTS errors …`.                                                                                               |
| **CI**           | Установить `pytest --log-cli-level=INFO`; новые тесты входят в общий suite.                                                                                 |
| **Lint / mypy**  | Добавить `services/error_service.py` в `mypy.ini strict`.                                                                                                   |

---

#### 4. **P — Push**

```bash
git add .
git commit -m "feat(ux): graceful provider errors with inline model picker & /admin errors summary"
git push origin main
```

---

#### Результат итерации

| Артефакт / Функция                     | Статус после Iter 14                 |
| -------------------------------------- | ------------------------------------ |
| `safe_generate()`                      | единая точка вызова провайдеров      |
| Пользовательское уведомление об ошибке | выводится + кнопка «📋 Модели»       |
| Контекст после ошибки                  | хранит только сообщение пользователя |
| Таблица `errors`                       | собирает ошибки за 24 ч              |
| Команда `/admin errors`                | выводит агрегированную сводку        |
| Тест-набор `test_fallback.py`          | зелёный                              |
| Документация / CHANGELOG               | обновлены                            |
| CI (lint + tests + docker-dry-run)     | зелёные                              |
