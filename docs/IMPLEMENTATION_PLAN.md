### Итерация 2 — **Authorization Flow**

> **Исходное состояние после Iter 1**
>
> * Схема БД уже содержит `users / requests / responses / models`. Однако в `users` пока **нет** поля `is_active`.
> * Базовый бот (`/start`) и `/ping` есть; хендлеры подключены через `create_bot_and_dispatcher` .
> * В CI — lint, tests, docker-dry-run настроены.
> * Токен Telegram читается из `BOT_TOKEN` (.env) и в тестах мокается.

Цель итерации — полноценная авторизация с заявкой пользователя и подтверждением админом внутри бота.

---

#### 1. **T — Test first**

1. **Новый файл** `tests/bot/test_auth.py`.
2. Фикстуры:

   * `admin_id = 999` (подменяется через `monkeypatch.setenv("ADMIN_CHAT_ID", "999")`).
   * Мокирование `Message.answer` и `Bot.send_message` (также как в `test_start.py`) для отлова исходящих сообщений.
3. **Сценарий «незарегистрированный пользователь»**:

   1. Вызываем `/start` от пользователя `uid = 123`.
   2. Ожидаем один ответ в личку: *«Ваша заявка отправлена администратору»*.
   3. Проверяем, что боту отправлено **второе** сообщение в админ-чат `999` с кнопкой «✅ Одобрить».
   4. Запрос к БД: строка в `users` существует, `is_active == 0`.
4. **Сценарий «одобрение админом»**:

   1. Синтетически шлём `/admin approve 123` от юзера 999.
   2. Проверяем, что:

      * Юзеру 123 уходит сообщение *«Доступ открыт»*.
      * В `users` поле `is_active == 1`.
   3. Повторно шлём от 123 любую команду `/ping` → бот отвечает «Bot ready» (контроль, что middleware пропускает).
5. Тест пока падает: нет middleware, нет команд, нет столбца `is_active`.

---

#### 2. **F — Feature**

1. **Расширить схему БД**

   * Добавить в `CREATE_USERS` поле `is_active INTEGER NOT NULL DEFAULT 0`.
   * Если таблица уже существует, выполнить `ALTER TABLE users ADD COLUMN is_active …` (упростить: перегенерировать файл для тестовой БД).
   * Добавить поле `requested_at TIMESTAMP` (опционально — для статистики).
2. **Сервис `user_service.py`**

   * `async def get_or_create_user(tg_id, name)` → возвращает объект + `is_active`.
   * `async def set_active(tg_id, value: bool)`.
   * `async def pending_users()` → список заявок.
3. **Middleware `AuthMiddleware`**

   * При каждом апдейте сверяет `is_active`.
   * Если пользователь не найден → создаёт запись и шлёт «заявка отправлена» + уведомление админ-чату.
   * Если `is_active == 0` → игнорирует любые другие команды кроме `/start`.
4. **Админ-команды**

   * Роутер `admin_router` с фильтром `lambda msg: msg.chat.id == ADMIN_CHAT_ID`.
   * `/admin approve <tg_id>` → дергает `set_active`.
   * `/admin users pending` — список заявок (подготовка к Iter 7).
   * Пароль‐login **не нужен** (админ определяется chat-id).
5. **Inline-кнопка в уведомлении**

   * Когда заявка поступает, бот в чат ADMIN\_CHAT\_ID шлёт сообщение с инлайн-кнопкой «✅ Одобрить».
   * Callback-handler исполняет то же, что и `/admin approve`.
6. **Обновить `create_bot_and_dispatcher`**

   * Подключить middleware и новые роутеры.
   * Прокинуть `ADMIN_CHAT_ID` из env по умолчанию «0» (для тестов подменяется).
7. **README** кратко объяснить процесс авторизации.

После реализации запустить `pytest` — зелёный.

---

#### 3. **I — Integrate**

1. **Док-строки**: в `user_service.py` расписать бизнес-правила статусов.
2. **pre-commit**: добавить mypy-check на новый пакет `services/*`.
3. **CI**: никаких изменений, тесты сами подхватятся.
4. **ER-диаграмма** в `database.py` обновить (добавить `is_active`).

---

#### 4. **P — Push**

```bash
git add .
git commit -m "feat(auth): add approval workflow and auth middleware"
git push origin main
```

---

#### Результат итерации

| Артефакт / Функция               | Статус после Iter 2                   |
| -------------------------------- | ------------------------------------- |
| Столбец `users.is_active`        | добавлен (0/1)                        |
| Middleware `AuthMiddleware`      | блокирует неактивных                  |
| Админ-команда & inline «approve» | работают                              |
| Тест `tests/bot/test_auth.py`    | зелёный                               |
| Текущие команды пользователя     | обрабатываются только после одобрения |
| CI                               | lint + tests + docker OK              |
