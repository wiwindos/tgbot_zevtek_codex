# Deploy

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill variables.
3. Run `make compose-up`.
4. Ensure container status is `healthy` via `docker compose ps`.
5. Run `make compose-down` to stop services.
