import json
import subprocess
import time

import pytest

pytestmark = pytest.mark.docker

COMPOSE_FILE = "deploy/docker-compose.dev.yml"


def test_compose_service_health(tmp_path):
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d"],
        check=True,
    )
    try:
        container_id = (
            subprocess.check_output(
                [
                    "docker",
                    "compose",
                    "-f",
                    COMPOSE_FILE,
                    "ps",
                    "-q",
                ]
            )
            .decode()
            .strip()
        )
        for _ in range(10):
            inspect = subprocess.check_output(
                ["docker", "inspect", container_id]
            )  # noqa: E501
            data = json.loads(inspect)[0]
            health = data["State"].get("Health", {}).get("Status")
            if health == "healthy":
                break
            time.sleep(3)
        assert health == "healthy"
    finally:
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "down"],
            check=False,
        )
