FROM python:3.11-slim

ARG BUILD_ENV=prod
ARG VERSION=dev
ENV TZ=Europe/Berlin

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN adduser --disabled-password --gecos "" bot && chown -R bot /app
USER bot

EXPOSE 8080
ENTRYPOINT ["./scripts/entrypoint.sh"]
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8080/ping || exit 1
LABEL org.opencontainers.image.version=$VERSION
