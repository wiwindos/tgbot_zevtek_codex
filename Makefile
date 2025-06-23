docker-build:
	docker build -t bot:local .

docker-run:
	docker run -it --rm -p 8080:8080 bot:local

compose-up:
	docker compose -f deploy/docker-compose.dev.yml up -d

compose-down:
	docker compose -f deploy/docker-compose.dev.yml down

docker-push:
	docker push ghcr.io/example/tgbot:latest
