FROM python:3.11-slim

ARG VERSION=unknown

WORKDIR /app

RUN adduser --disabled-password --gecos "" bot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER bot

EXPOSE 8080

HEALTHCHECK --interval=30s --start-period=30s --retries=3 CMD ["python", "-m", "bot.main", "--ping"]

ENTRYPOINT ["python", "-m", "bot.main"]
LABEL org.opencontainers.image.version=$VERSION

