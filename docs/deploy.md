# Deploy guide

1. Clone the repo and copy `.env.example` to `.env`.
2. Run `make compose-up`.
3. Verify health via `curl http://localhost:8080/ping`.
4. Stop services with `make compose-down`.

