docker-build:
docker build -t tgbot:dev .

docker-run:
docker run --rm -p 8080:8080 tgbot:dev

compose-up:
docker compose -f deploy/docker-compose.dev.yml up -d

compose-down:
docker compose -f deploy/docker-compose.dev.yml down

docker-push:
docker build -t ghcr.io/$$REPOSITORY:$$TAG . && docker push ghcr.io/$$REPOSITORY:$$TAG

