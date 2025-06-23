import os
import subprocess
import time

import pytest

IMAGE_TAG = "tgbot:test"
COMPOSE_FILE = "deploy/docker-compose.dev.yml"


def has_docker() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


@pytest.fixture(scope="module")
def skip_if_no_docker():
    if not has_docker():
        pytest.skip("docker not available")


@pytest.mark.usefixtures("skip_if_no_docker")
def test_build_and_run_image(tmp_path):
    subprocess.check_call(["docker", "build", "-t", IMAGE_TAG, "."])
    env = {
        "BOT_TOKEN": "123:TEST",
        "ADMIN_CHAT_ID": "1",
        "LOG_LEVEL": "INFO",
        "TZ": "Europe/Berlin",
    }
    cmd = ["docker", "run", "-d", "--rm"]
    for k, v in env.items():
        cmd += ["-e", f"{k}={v}"]
    cmd.append(IMAGE_TAG)
    container_id = subprocess.check_output(cmd).decode().strip()
    try:
        for _ in range(20):
            logs = subprocess.check_output(
                [
                    "docker",
                    "logs",
                    container_id,
                ]
            ).decode()
            if "bot_started" in logs:
                break
            time.sleep(1)
        else:
            raise AssertionError("bot did not start")
    finally:
        subprocess.check_call(["docker", "stop", container_id])


@pytest.mark.usefixtures("skip_if_no_docker")
def test_docker_compose(tmp_path):
    data_dir = tmp_path / "data"
    env = os.environ.copy()
    env.update(
        {
            "BOT_TOKEN": "123:TEST",
            "ADMIN_CHAT_ID": "1",
            "LOG_LEVEL": "INFO",
            "TZ": "Europe/Berlin",
        }
    )
    subprocess.check_call(
        [
            "docker",
            "compose",
            "-f",
            COMPOSE_FILE,
            "up",
            "-d",
            "--build",
        ],
        env=env,
    )
    try:
        for _ in range(20):
            out = subprocess.check_output(
                [
                    "docker",
                    "compose",
                    "-f",
                    COMPOSE_FILE,
                    "ps",
                    "--format",
                    "json",
                ]
            )
            if b"healthy" in out:
                break
            time.sleep(1)
        else:
            raise AssertionError("compose service not healthy")
        assert data_dir.exists()
    finally:
        subprocess.check_call(
            [
                "docker",
                "compose",
                "-f",
                COMPOSE_FILE,
                "down",
            ]
        )
