### Итерация 3 — **Context Buffer & Message Splitting**


---

#### 1. T — **Test first**

| Действие                      | Детали                                                                                                                                                                 |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Файл**                      | `tests/test_context.py`                                                                                                                                                |
| **Фикстуры**                  | Скопируйте стиль `tests/test_start.py`: мокируйте `Message.answer` через `monkeypatch`, импортируйте фабрику как:<br>`from bot.main import create_bot_and_dispatcher`. |
| **Сценарий 1 «history»**      | Отправьте три текста (`one`, `two`, `three`) → убедитесь, что внутренняя очередь истории для чата содержит 3 пар (role, text).                                         |
| **Сценарий 2 «/clear»**       | Отправьте `/clear` → проверка, что очередь очищена (длина 0).                                                                                                          |
| **Сценарий 3 «split > 4096»** | Смоделируйте ответ в 6000 симв. (строка `"x"*6000`); мок проверяет, что `answer` вызван 2 раза, а суммарный текст совпадает с исходным.                                |
| **Ожидание**                  | Все тесты падают — функциональность не реализована.                                                                                                                    |

---

#### 2. F — **Feature**

| №   | Шаг                   | Расположение / имя                                                                                                                                                                                                                          |
| --- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 | **Контекст-буфер**    | `services/context.py`<br>`python<br>class ContextBuffer:<br>    def __init__(..., max_messages=20): ...<br>`                                                                                                                                |
| 2.2 | **Middleware**        | `bot/context_middleware.py` (или внутри `middleware.py`)<br>*Ставит в цепочку после `AuthMiddleware`;* записывает входящие и исходящие сообщения через буфер.                                                                               |
| 2.3 | **Утилита дробления** | `bot/utils.py` → `async def send_long_message(bot, chat_id, text)` с использованием `textwrap.wrap(..., width=4096)`.                                                                                                                       |
| 2.4 | **Команда `/clear`**  | Новый роутер `bot/conversation.py` (или расширяем существующий):<br>`python<br>@router.message(Command(commands=['clear']))<br>async def clear_ctx(...):<br>    buffer.clear(chat_id)<br>    await message.answer('Контекст очищен ✅')<br>` |
| 2.5 | **Интеграция**        | В `create_bot_and_dispatcher()`:<br>`python<br>dp.message.middleware(ContextMiddleware(buffer))<br>dp.include_router(conversation_router)<br>`                                                                                              |
| 2.6 | **Замена ответов**    | В `/start`, `/ping` и будущих хендлерах — вместо `message.answer()` вызвать `send_long_message(...)`.                                                                                                                                       |
| 2.7 | **Конфиг**            | В `.env.example` добавить `MAX_CONTEXT_MESSAGES=20`; считывать через `int(os.getenv(...))`.                                                                                                                                                 |

---

#### 3. I — **Integrate**

| Задача         | Детали                                                                              |
| -------------- | ----------------------------------------------------------------------------------- |
| **Док-строки** | Подробное описание буфера и алгоритма дробления в `services/context.py`.            |
| **README**     | Раздел “Context management & limits”: зачем нужен `/clear`, лимит 4096 симв. и т.д. |
| **pre-commit** | Убедиться, что новые файлы проходят `black`, `isort`, `flake8`, `mypy`.             |
| **CI**         | Тесты уже исполняются — изменений не требуется.                                     |

---

#### 4. P — **Push**

```bash
git add .
git commit -m "feat(conversation): add per-chat context buffer and safe message splitting"
git push origin master
```

---

### Результат итерации

| Компонент / Функция                | Итоговое состояние                    |
| ---------------------------------- | ------------------------------------- |
| `services/context.py`              | Буфер сообщений per-chat              |
| `ContextMiddleware`                | Сохраняет историю, очищается `/clear` |
| `send_long_message`                | Делит ответы > 4096 симв.             |
| Команда `/clear`                   | Работает                              |
| Тест-набор `tests/test_context.py` | Зелёный                               |
| `.env.example`, README             | Обновлены                             |
| CI (lint + tests + docker)         | Проходит                              |

