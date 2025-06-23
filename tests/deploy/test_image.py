import json
import subprocess
import time

import pytest


@pytest.mark.docker
def test_docker_image_health(tmp_path):
    image = "bot:test"
    subprocess.run(["docker", "build", "-t", image, "."], check=True)
    container_name = "bot_test_container"
    subprocess.run(
        ["docker", "run", "-d", "--name", container_name, image],
        check=True,
    )
    try:
        for _ in range(10):
            inspect = subprocess.check_output(
                ["docker", "inspect", container_name]
            )  # noqa: E501
            data = json.loads(inspect)[0]
            health = data["State"].get("Health", {}).get("Status")
            if health == "healthy":
                break
            time.sleep(3)
        assert health == "healthy"
    finally:
        subprocess.run(["docker", "stop", container_name], check=False)
        subprocess.run(["docker", "rm", container_name], check=False)
