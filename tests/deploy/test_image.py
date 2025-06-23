import os
import subprocess
import time

import pytest


@pytest.fixture(autouse=True, scope="module")
def check_docker():
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pytest.skip("Docker not available")


def _wait_health(container_id: str, timeout: int = 30) -> bool:
    for _ in range(timeout):
        res = subprocess.run(
            [
                "docker",
                "inspect",
                "-f",
                "{{.State.Health.Status}}",
                container_id,
            ],
            capture_output=True,
            text=True,
        )
        if res.stdout.strip() == "healthy":
            return True
        time.sleep(1)
    return False


def test_image_builds_and_runs(tmp_path):
    image = "tgbot:test"
    subprocess.run(["docker", "build", "-t", image, "."], check=True)
    container_id = (
        subprocess.check_output(
            [
                "docker",
                "run",
                "-d",
                image,
            ]
        )
        .decode()
        .strip()
    )
    try:
        assert _wait_health(container_id)
    finally:
        subprocess.run(["docker", "stop", container_id], check=False)
        subprocess.run(["docker", "rm", container_id], check=False)


def test_compose_up(tmp_path):
    compose_file = "deploy/docker-compose.dev.yml"
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            compose_file,
            "up",
            "-d",
            "--build",
        ],
        check=True,
    )
    container_id = (
        subprocess.check_output(
            [
                "docker",
                "compose",
                "-f",
                compose_file,
                "ps",
                "-q",
                "bot",
            ]
        )
        .decode()
        .strip()
    )
    try:
        assert _wait_health(container_id)
        assert os.path.isdir("data")
    finally:
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                compose_file,
                "down",
            ],
            check=False,
        )
