# Deploying with Docker

Build and run locally:

```bash
make docker-build
make docker-run
```

Using Compose for development:

```bash
make compose-up
```

For production, use `deploy/docker-compose.prod.yml` referencing the published image.

