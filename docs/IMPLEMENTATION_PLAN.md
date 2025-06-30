### Итерация 12 — **Provider Picker & Inline Model Selector**

> **Исходное состояние после Iter 11**
>
> * Провайдеры `GeminiProvider`, `MistralProvider`, `DeepseekProvider` уже имплементированы и зарегистрированы в `ProviderRegistry`.
> * Бот хранит текущую **модель** в памяти (`ContextBuffer.model`) и переключает её текстовой командой `/model <name>`.
> * Провайдер при смене модели иногда «перетягивает» пользователя на другого провайдера (ошибка UX).
> * Пользователь не может посмотреть **список моделей** отдельно для каждого провайдера.
> * Переключение провайдера пока возможно только через переменную `.env` `DEFAULT_MODEL` или /admin-refresh.

**Цель итерации — внедрить полноценный UI выбора провайдера (команда `/providers`) и моделей (команда `/models`) через inline-кнопки, гарантировав сохранение контекста и корректную привязку «провайдер ↔ модель» на пользователя.**

---

#### 1. **T — Test first**

1. **Новый файл** `tests/bot/test_provider_switch.py`.
2. **Фикстуры**:

   * `user_id = 101`, `admin_id = 999`.
   * `available_models`: заглушка реестра:

     ```python
     {"deepseek": ["deepseek-base", "deepseek-large"],
      "mistral": ["mistral-small", "mistral-medium"],
      "gemini":  ["gemini-pro", "gemini-1.5-pro"]}
     ```
3. **Сценарий A «Выбор провайдера»**

   1. Пользователь шлёт `/providers` → бот отправляет inline-кнопки Deepseek / Mistral / Gemini.
   2. Нажимаем «Mistral»; проверяем callback-answer «Провайдер переключён на *Mistral*».
   3. `context.user_provider[user_id] == "mistral"`.
4. **Сценарий B «Список моделей текущего провайдера»**

   1. После A шлём `/models`; бот выводит **только** `["mistral-small", "mistral-medium"]`.
   2. Нажимаем «mistral-medium»; проверяем:

      * `context.user_model[user_id] == "mistral-medium"`
      * Провайдер остаётся `"mistral"`.
5. **Сценарий C «Возврат к прежнему провайдеру»**

   1. Снова `/providers` → выбираем «Gemini», `/models` выводит список Gemini.
   2. Затем снова `/providers` → «Mistral». Ожидаем, что модель восстановилась `mistral-medium`.
6. **Сценарий D «Смена модели не меняет провайдера»**

   1. При активном провайдере Gemini жмём `/models` → выбираем `gemini-pro`;
   2. Проверяем, что `context.user_provider` всё ещё `"gemini"`.
7. Все тесты **красные** до реализации.

---

#### 2. **F — Feature**

1. **Структура данных для выбора**

   * В `services/context.py` добавить:

     ```python
     user_provider: dict[int, str]           # текущий провайдер
     user_models: dict[int, dict[str, str]]  # {prov: last_model}
     ```
   * Хелперы: `get_provider(user_id)`, `set_provider(user_id, prov)`, `get_model(user_id)`, `set_model(user_id, model)`.
2. **Команда `/providers`**

   * Хэндлер отправляет одно сообщение с inline-кнопками:
     `InlineKeyboardButton("Deepseek", callback_data="provider:deepseek")`, и т.д.
   * Callback-хэндлер `provider_cb_<prov>`:

     1. `set_provider(uid, prov)`.
     2. Если для этого провайдера уже была модель → восстанавливаем, иначе берём дефолт (первую из `list_models`).
     3. Ответ-уведомление (`answer_callback_query`) и `edit_message_text` «Провайдер переключён…».
3. **Команда `/models`**

   * Проверить выбранный провайдер; если `None` → предложить сначала `/providers`.
   * Запрос `ProviderRegistry.list_models(prov)` → выдаёт список; выводим 1–5 кнопок в ряд.
   * Callback `model_cb:<name>`:

     1. `set_model(uid, name)` (и заодно `set_provider` по префиксу, но провайдер уже выбран).
     2. Подтверждаем пользователю «Модель *<name>* активна».
     3. Никаких скрытых side-effects (контов не трогаем).
4. **Адаптация провайдеров**

   * В каждом провайдере: свойство `self.model`; метод `set_model(name)`.
   * `ProviderRegistry.get()` возвращает уже сконфигурированный инстанс с нужной моделью.
   * Для Deepseek, если API не принимает `model`, оставить как есть, но всё равно сохранять выбор (для консистентности).
5. **Гарантия сохранения контекста**

   * Контекст (`buffer.messages`) **не** очищается при смене модели/провайдера.
   * Доп. проверка в `generate_reply`: если провайдер сменился, но контекст есть, всё равно передаём его новому провайдеру.
6. **Обработка ошибок**

   * Если `list_models()` → `[]` или API-ошибка, бот отвечает «Модели недоступны, попробуйте позже».
   * Callback-хэндлер ловит исключения, шлёт `answer_callback_query` c `show_alert=True`.
7. **Тесты** предыдущего раздела теперь проходят.

---

#### 3. **I — Integrate**

1. **Документация**

   * README:

     * Новый раздел «🔄 Переключение провайдера и модели».
     * GIF-скрин (сделаем в Iter 18) — пока TODO.
   * CONTEXT.md — диаграмма «User → Provider ↔ Model».
   * HELP / /start тексты: добавить `/providers`, `/models`.
2. **pre-commit**

   * Обновить `mypy.ini`, добавить `services/context.py` в strict-mypy-path.
3. **CI**

   * Шаг `aiogram-testing` (Docker service) оставляем; новые тесты автоматически подхватываются.
   * Добавить job `grep legacy refs` (из Iter 11) на `"provider:"` префиксы в callback — не критично, но полезно.
4. **Миграций БД нет** — данные хранятся in-memory.

---

#### 4. **P — Push**

```bash
git add .
git commit -m "feat(ui): inline provider & model picker with per-user persistence"
git push origin main
```

---

#### Результат итерации

| Артефакт / Функция                   | Статус после Iter 12                                      |
| ------------------------------------ | --------------------------------------------------------- |
| `/providers`                         | выводит кнопки, сохраняет выбранный провайдер             |
| `/models`                            | показывает модели текущего провайдера, переключает модель |
| `ContextStorage.user_provider`       | реализовано                                               |
| `ContextStorage.user_models`         | запоминает последнюю модель на провайдер                  |
| Смена модели ≠ смена провайдера      | гарантировано                                             |
| UX-ошибка «модель меняет провайдера» | устранена                                                 |
| Тест-suite `test_provider_switch.py` | зелёный                                                   |
| Документация                         | синхронизирована (README, HELP)                           |
| CI                                   | lint + tests + docker-dry-run — зелёные                   |
