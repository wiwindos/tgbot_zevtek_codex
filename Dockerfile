FROM python:3.11-slim

ARG BUILD_ENV=prod
ARG VERSION=0.0.0
ENV PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY bot ./bot
COPY providers ./providers
COPY scheduler ./scheduler
COPY services ./services
COPY logging_config.py ./logging_config.py

EXPOSE 8080
HEALTHCHECK CMD ["python", "-m", "bot.main", "--ping"]

LABEL version=$VERSION

USER nobody
ENTRYPOINT ["/app/entrypoint.sh"]

