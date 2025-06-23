FROM python:3.11-slim

ARG BUILD_ENV=prod
ARG VERSION=0.1.0
LABEL org.opencontainers.image.version=$VERSION

WORKDIR /app

RUN adduser --disabled-password --gecos "" bot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER bot
HEALTHCHECK CMD ["python", "-m", "bot.main", "--ping"]
CMD ["python", "-m", "bot.main"]
