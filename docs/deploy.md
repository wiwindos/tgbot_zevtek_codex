# Deploy guide

1. Clone the repo
2. Copy `.env.example` to `.env` and fill variables
3. Run `docker-compose -f deploy/docker-compose.dev.yml up -d --build`
4. Visit logs with `docker-compose logs -f`
5. For production use `docker-compose -f deploy/docker-compose.prod.yml up -d`
