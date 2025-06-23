import json
import subprocess
import time

import pytest

tag = "bot:test"
container_name = "bot_test"


@pytest.mark.docker
def test_docker_image_health():
    subprocess.check_call(["docker", "build", "-t", tag, "."])
    container_id = (
        subprocess.check_output(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                tag,
            ]
        )
        .decode()
        .strip()
    )
    try:
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
        subprocess.call(["docker", "stop", container_id])
        subprocess.call(["docker", "rm", container_id])
