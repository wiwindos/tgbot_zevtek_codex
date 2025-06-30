### Итерация 13 — **Gemini Multimodal File Pipeline**

> **Исходное состояние после Iter 12**
>
> * Бот принимает вложения, сохраняет их на диск, но дальше просто отвечает «Эта модель не поддерживает файлы» (кроме устаревшей stub-логики).
> * `GeminiProvider.generate()` умеет только text-prompt: пытается вставить `file_bytes` в `parts`, но SDK Google GenAI отвергает запрос (ошибки 400 / invalid part type).
> * Модели Deepseek / Mistral файлов не поддерживают и должны продолжать вежливо отказываться.
> * Размер файла и MIME-тип никак не валидируются; очень большие файлы могут заблокировать бот.

**Цель итерации — реализовать полноценную мультимодальную обработку в провайдере Gemini:**

1. принимать изображения (JPEG/PNG), аудиофайлы (WAV/MP3) и простые текстовые / PDF-файлы;
2. корректно формировать запрос к API Gemini 1.5;
3. вводить мягкие ограничения на размеры, MIME-типы и graceful-отказы;
4. обновить юнит-/интеграционные тесты и документацию.

---

#### 1. **T — Test first**

1. **Новый файл** `tests/bot/test_file_gemini.py`.
2. **Фикстуры**

   * `user_provider = "gemini"` (через команду `/providers`).
   * Стаб `fake_image = Path("tests/fixtures/cat.png").read_bytes()` (<150 kB).
   * `fake_audio = Path("tests/fixtures/hello.wav").read_bytes()` (\~80 kB).
   * `fake_big_pdf = b"x" * 900_000`  (\~900 kB > лимита).
   * Мок `google.generativeai.GenerativeModel.generate_content` возвращает `Dummy` со строкой "image received" / "audio received".
3. **Сценарии**

   * **A (OK - image)** — отправляем `cat.png`, ожидаем:

     * GeminiProvider зовётся c base64-image;
     * ответ пользователя содержит «image received».
   * **B (OK - audio)** — отправляем `hello.wav`, ожидаем: «audio received».
   * **C (File too big)** — отправляем `big.pdf`, бот отвечает «Файл слишком велик … (≤ 512 kB)».
   * **D (Unsupported MIME на Deepseek)** — переключаем провайдер на Deepseek, шлём `cat.png`, бот отвечает «Эта модель не принимает файлы».
4. Все тесты пока *красные*.

---

#### 2. **F — Feature**

1. **`file_service.py` расширение**

   * Функция `detect_mime(bytes) -> str` (использовать `python-mime` или `magic.from_buffer`).
   * Константы:

     ```python
     MAX_FILE_SIZE = 512_000  # 512 kB
     ALLOWED_IMAGE = {"image/png", "image/jpeg"}
     ALLOWED_AUDIO = {"audio/wav", "audio/x-wav", "audio/mpeg"}
     ALLOWED_TEXT  = {"text/plain", "application/pdf"}
     ```
   * Возврат Enum `FileKind.IMAGE|AUDIO|TEXT|UNSUPPORTED`.
   * Guard size: если `len(file_bytes) > MAX_FILE_SIZE` → raise `FileTooLarge`.
2. **`GeminiProvider.generate()` мультимодальный input**

   * Вход: `prompt:str, file: Optional[FilePayload]`.
   * Если `file is None` → старый поток.
   * Для IMAGES / AUDIO:

     ```python
     image_part = {"mime_type": mime, "data": base64.b64encode(file_bytes).decode()}
     prompt_parts = [prompt, image_part]
     model.generate_content(prompt_parts, stream=False)
     ```
   * Для TEXT / PDF:

     * PDF: извлечь первые N символов (`pdfplumber`), текст усечь до max\_tokens≈3000.
     * Добавить в prompt блок `"""<extracted text>"""`.
   * Флаг `supports_files = True`, sub-flags: `supports_image`, `supports_audio`, `supports_text`.
3. **Расширить `ProviderRegistry.list_models()`**

   * Возвращать `model.meta = {"supports_files":True, "supports_image":…}` — пригодится фронту.
4. **`file_handlers.py`**

   * После сохранения файла → `kind = detect_mime(...)`.
   * Проверить:

     * выбранный провайдер `prov` имеет `supports_files` **и** `supports_<kind>`;
     * иначе вежливый отказ.
   * Обработка исключений `FileTooLarge`, `UnsupportedMime`, `GenAIError` (отправка понятного сообщения).
5. **Deepseek / Mistral**

   * Явно `supports_files = False`. Старый код отказа оставить.
6. **Логирование**

   * `structlog.info("file_received", kind, size, mime, provider, model, user_id)`.
   * При ошибке > warning.

---

#### 3. **I — Integrate**

1. **Документация**

   * README: таблица поддерживаемых типов («Gemini 1.5 Pro — изображения ✓ / аудио ✓ / текст-PDF ✓»).
   * `docs/file_handling.md` — пошаговые примеры с PNG, MP3, PDF; ограничения размера.
   * /help — дописать фразу «Для обработки файлов выберите провайдера Gemini».
2. **CHANGELOG**

   * **Added** — «Multimodal file support (Gemini)».
   * **Fixed** — «Graceful oversize file rejection».
3. **pre-commit / CI**

   * Добавить линтер `pydocstyle` к новым функциям.
   * `tests/fixtures` вложить изображения + audio; GH Actions `actions/upload-artifact` not needed, committed tiny files ≤20 kB.
4. **Dependencies**

   * `poetry add python-magic pdfplumber`.
   * `requirements.txt` синхронизировать; добавить note в **dev-shell.nix**.
5. **Security note**

   * Проверить, что сохраняемые файлы пишутся в `/data/files/<uuid>.<ext>` с chmod 600 (umask). Зачистка TMP не требуется пока; TODO Iter 19.

---

#### 4. **P — Push**

```bash
git add .
git commit -m "feat(gemini): multimodal image/audio/text file support with size guard"
git push origin main
```

---

#### Результат итерации

| Артефакт / Функция                 | Статус после Iter 13                           |
| ---------------------------------- | ---------------------------------------------- |
| `GeminiProvider`                   | приём JPEG/PNG, WAV/MP3, PDF/TXT               |
| Размерное ограничение ≤ 512 kB     | реализовано, oversize → вежливый отказ         |
| `file_service.detect_mime()`       | определяет MIME, Enum FileKind                 |
| Отказ Deepseek / Mistral           | корректный, UX-сообщение «модель не принимает» |
| Тест-набор `test_file_gemini.py`   | зелёный                                        |
| README + docs/file\_handling.md    | обновлены, примеры & лимиты                    |
| CI (lint + tests + docker-dry-run) | зелёные                                        |
| CHANGELOG                          | зафиксировано «Added: multimodal Gemini»       |
