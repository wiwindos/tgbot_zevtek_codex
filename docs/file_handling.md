# File handling

The bot can pass small files to the Gemini provider. Supported formats:

- PNG and JPEG images
- OGG/WAV/MP3 audio
- Plain text or PDF documents

Files larger than **512 kB** are rejected with a short message.

Example session:

```
/user sends cat.png
→ image received
```

To try audio use `tests/fixtures/hello world.ogg`.
