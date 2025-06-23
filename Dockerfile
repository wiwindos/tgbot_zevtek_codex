FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" bot
USER bot

COPY . .

EXPOSE 8080

HEALTHCHECK --interval=30s --start-period=30s --retries=3 CMD python -m bot.main --ping || exit 1

LABEL org.opencontainers.image.version=$VERSION

ENTRYPOINT ["python", "-m", "bot.main"]
