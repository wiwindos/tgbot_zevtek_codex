FROM python:3.11-slim

ARG BUILD_ENV=prod
ARG VERSION=dev
ENV TZ=Europe/Berlin

WORKDIR /app
COPY requirements.txt .
# hadolint ignore=DL3008,DL3015
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN adduser --disabled-password --gecos "" bot && chown -R bot /app
USER bot

EXPOSE 8080
ENTRYPOINT ["./scripts/entrypoint.sh"]
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8080/ping || exit 1
LABEL org.opencontainers.image.version=$VERSION
