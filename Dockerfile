FROM python:3.11-slim AS builder
ARG VERSION=unknown

WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN pre-commit run --files bot database.py || true
RUN pytest -m "not docker" -q && mypy

FROM python:3.11-slim AS runtime
ARG VERSION=unknown
ENV DB_PATH=/app/data/bot.db
WORKDIR /app
RUN adduser --disabled-password --gecos "" bot
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=builder /app /app
VOLUME /app/data
USER bot
EXPOSE 8080
HEALTHCHECK CMD python -m bot.main --ping || exit 1
ENTRYPOINT ["python", "-m", "bot.main"]
LABEL org.opencontainers.image.version=$VERSION

