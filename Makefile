compose-up:
	docker compose -f deploy/docker-compose.dev.yml up -d --build

compose-down:
	docker compose -f deploy/docker-compose.dev.yml down

docker-build:
	docker build -t tgbot:dev .

docker-push:
	docker push tgbot:dev
