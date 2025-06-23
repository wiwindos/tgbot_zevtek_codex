compose-up:
docker compose -f deploy/docker-compose.dev.yml up -d --build

compose-down:
docker compose -f deploy/docker-compose.dev.yml down

build-image:
docker build -t tgbot:local .

push-image:
docker push tgbot:local

