# Docker images

This project uses a multi-stage Dockerfile.

- **builder** installs development dependencies, runs tests and mypy.
- **runtime** contains only production packages and the application files.

The development compose file builds the `builder` stage so you can run tests inside the container.
Production compose pulls the prebuilt runtime image from GHCR.

Two requirements files separate packages:

- `requirements.txt` — runtime dependencies.
- `requirements-dev.txt` — runtime + lint/test tools.
