import json
import subprocess
import time

import pytest

compose_file = "deploy/docker-compose.dev.yml"


@pytest.mark.docker
def test_compose_up_health():
    subprocess.check_call(
        [
            "docker",
            "compose",
            "-f",
            compose_file,
            "build",
        ]
    )
    subprocess.check_call(
        [
            "docker",
            "compose",
            "-f",
            compose_file,
            "up",
            "-d",
        ]
    )
    try:
        container_id = (
            subprocess.check_output(
                [
                    "docker",
                    "compose",
                    "-f",
                    compose_file,
                    "ps",
                    "-q",
                ]
            )
            .decode()
            .strip()
        )
        status = ""
        for _ in range(30):
            out = subprocess.check_output(
                [
                    "docker",
                    "inspect",
                    "-f",
                    "{{json .State.Health.Status}}",
                    container_id,
                ]
            )
            status = json.loads(out.decode())
            if status == "healthy":
                break
            time.sleep(1)
        assert status == "healthy"
    finally:
        subprocess.call(["docker", "compose", "-f", compose_file, "down"])
