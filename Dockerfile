FROM python:3.11-slim
ARG VERSION=unknown
ENV DB_PATH=/app/data/bot.db
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data && adduser --disabled-password --gecos "" bot && chown -R bot:bot /app/data
VOLUME /app/data
USER root
RUN apt-get update && apt-get install -y proxychains4 && rm -rf /var/lib/apt/lists/*
USER bot

COPY deploy/proxychains.conf /etc/proxychains.conf
EXPOSE 8080
HEALTHCHECK CMD proxychains4 python -m bot.main --ping || exit 1
ENTRYPOINT ["proxychains4", "python", "-m", "bot.main"]
LABEL org.opencontainers.image.version=$VERSION

