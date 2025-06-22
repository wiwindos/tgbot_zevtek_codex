### Итерация 5 — **Scheduler for Model Auto-Refresh**

*(T – F – I – P план; синхронизирован с текущей структурой репо `wiwindos/tgbot_zevtek_codex`)*

---

#### Текущее состояние репозитория (master)

| Факт                                                                                                                                     | Файл / каталог                               |
| ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Базовый бот, middlewares и команда `/ping` присутствуют.                                                                                 | `bot/…` ([github.com][1])                    |
| Таблица `models` уже создана в SQLite (Iter 1).                                                                                          | `bot/database.py`                            |
| Плуг-ин-слой провайдеров реализован (Iter 4): `providers/` с `ProviderRegistry`, `GeminiProvider`, `MistralProvider`, `DipseekProvider`. | `providers/…` (появился после последнего PR) |
| Уведомления админу отправляются через `ADMIN_CHAT_ID`; в тестах мокируется `Bot.send_message`.                                           | `bot/main.py`, `tests/…`                     |
| Пока **нет** периодической службы, которая обновляет таблицу `models`.                                                                   | —                                            |

---

## 1. T — **Test first**

| Шаг                            | Детали                                                                                                                                                                                                                                                                            |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Файл**                       | `tests/scheduler/test_refresh.py`                                                                                                                                                                                                                                                 |
| **Fixtures**                   | • Временный `bot.db` (tmpdir + `init_db()`);<br>• `provider_registry` c моками: `GeminiProvider.list_models` → `[\"g-1\"]`, `MistralProvider.list_models` → `[\"m-1\"]`, `DipseekProvider.list_models` → `[\"d-1\"]`.<br>• Мок `Bot.send_message` для отлова уведомлений.         |
| **Тест 1 «первое заполнение»** | Запустить `await pull_and_sync_models(registry)`. <br>Ожидание: в таблице `models` ровно 3 строк, уведомлений **0** (первичное создание молчит).                                                                                                                                  |
| **Тест 2 «детект изменений»**  | 1. Повторно замокать `MistralProvider.list_models` → `[\"m-2\"]` (модель поменялась).<br>2. Вызвать `pull_and_sync_models` снова.<br>3. Проверить:• таблица содержит 4 строки (`m-1` + `m-2`);<br>• `Bot.send_message` вызван **1 раз** и включает текст «обновлены модели: m-2». |
| Ожидание                       | Оба теста падают (пока нет scheduler-кода).                                                                                                                                                                                                                                       |

---

## 2. F — **Feature**

| №   | Задача                              | Файл / модуль                                                                                                                                                                                                                                                           |
| --- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 | **Служба**                          | Новый пакет `scheduler/`:<br>• `__init__.py`;<br>• `jobs.py` c `async def pull_and_sync_models(registry, db_path=DB_PATH): …`.                                                                                                                                          |
| 2.2 | **Алгоритм `pull_and_sync_models`** | 1. Для каждого провайдера → `list_models()`.<br>2. Сравнить с текущими строками `models` (по имени).<br>3. Добавить новые, обновить `updated_at` существующих.<br>4. Если diff ≠ Ø → `send_long_message(bot, ADMIN_CHAT_ID, f\"Обновлены модели: {', '.join(diff)}\")`. |
| 2.3 | **APScheduler**                     | `scheduler/runner.py`:<br>`python<br>scheduler = AsyncIOScheduler()<br>scheduler.add_job(pull_and_sync_models, CronTrigger(hour=0, minute=0))<br>`                                                                                                                      |
| 2.4 | **Старт сервиса**                   | В `create_bot_and_dispatcher()`:<br>`python<br>from scheduler.runner import scheduler<br>scheduler.start()  # после инициализации Bot/DP<br>`                                                                                                                           |
| 2.5 | **ENV-константы**                   | `.env.example` → добавить `REFRESH_CRON=\"0 0 * * *\"`; опционально `ENABLE_SCHEDULER=1`.                                                                                                                                                                               |
| 2.6 | **Requirements**                    | В `requirements.txt` добавить `APScheduler>=3.10`.                                                                                                                                                                                                                      |
| 2.7 | **Док-строки**                      | В `jobs.py` описать формат таблицы `models` и пример diff-уведомления.                                                                                                                                                                                                  |

---

## 3. I — **Integrate**

| Задача         | Детали                                                           |
| -------------- | ---------------------------------------------------------------- |
| **README**     | Раздел “Model auto-refresh”: как работает, как изменить cron.    |
| **pre-commit** | mypy-check `scheduler/*`.                                        |
| **CI**         | Тесты уже охватывают новый пакет; дополнительных шагов не нужно. |

---

## 4. P — **Push**

```bash
git add .
git commit -m "feat(scheduler): daily model sync and admin notification"
git push origin master
```

---

### Итог Iter 5

| Компонент / Функция        | Статус                                          |
| -------------------------- | ----------------------------------------------- |
| `scheduler/` + APScheduler | Запускает Cron-задачу                           |
| `pull_and_sync_models()`   | Обновляет таблицу `models`, уведомляет при diff |
| ENV `REFRESH_CRON`         | Добавлен                                        |
| Тесты `tests/scheduler/*`  | Зелёные                                         |
| README / pre-commit / CI   | Обновлены                                       |

