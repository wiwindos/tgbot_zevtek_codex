# Deployment

## Build and run

```bash
make docker-build
make docker-run
```

## Compose

```bash
docker compose -f deploy/docker-compose.dev.yml up -d
```

Production uses the image from GHCR defined in `docker-compose.prod.yml`.
