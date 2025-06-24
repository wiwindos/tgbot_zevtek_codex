import json
import subprocess
import time

import pytest

pytestmark = pytest.mark.docker

COMPOSE_FILE = "deploy/docker-compose.dev.yml"


def test_db_init_in_container(tmp_path):
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            COMPOSE_FILE,
            "up",
            "-d",
            "--build",
            "bot",
        ],
        check=True,
    )
    try:
        cid = (
            subprocess.check_output(
                [
                    "docker",
                    "compose",
                    "-f",
                    COMPOSE_FILE,
                    "ps",
                    "-q",
                    "bot",
                ]
            )
            .decode()
            .strip()
        )
        for _ in range(10):
            inspect = subprocess.check_output(["docker", "inspect", cid])
            data = json.loads(inspect)[0]
            health = data["State"].get("Health", {}).get("Status")
            if health == "healthy":
                break
            time.sleep(3)
        assert health == "healthy"
        subprocess.run(
            ["docker", "exec", cid, "ls", "/app/data/bot.db"],
            check=True,
        )
        logs = subprocess.check_output(["docker", "logs", cid]).decode()
        assert "OperationalError" not in logs
    finally:
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "down"],
            check=False,
        )


def test_no_dev_deps_in_prod(tmp_path):
    image = "tgbot:prod"
    subprocess.run(
        [
            "docker",
            "build",
            "-t",
            image,
            "--target",
            "runtime",
            ".",
        ],
        check=True,
    )
    result = subprocess.run(
        ["docker", "run", "--rm", image, "pip", "show", "pytest"],
        capture_output=True,
    )
    assert result.returncode != 0
