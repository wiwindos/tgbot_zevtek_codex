FROM python:3.11-slim

WORKDIR /app
RUN adduser --disabled-password --gecos "" botuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

HEALTHCHECK --interval=30s --start-period=30s --retries=3 \
  CMD python -m bot.main --ping || exit 1

USER botuser
ENTRYPOINT ["python", "-m", "bot.main"]
