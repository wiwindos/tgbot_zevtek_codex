import json
import os
import subprocess
import time
from pathlib import Path

import pytest


def wait_for_log(container_id: str, text: str, timeout: int = 20):
    for _ in range(timeout):
        logs = subprocess.check_output(
            [
                "docker",
                "logs",
                container_id,
            ]
        ).decode()
        if text in logs:
            return True
        time.sleep(1)
    return False


@pytest.mark.skipif(not Path("Dockerfile").exists(), reason="no docker")
def test_image_build_and_run(tmp_path):
    subprocess.run(["docker", "build", "-t", "tgbot:test", "."], check=True)
    cid = (
        subprocess.check_output(
            [
                "docker",
                "run",
                "-d",
                "-e",
                "BOT_TOKEN=dummy",
                "-e",
                "ADMIN_CHAT_ID=1",
                "-e",
                "LOG_LEVEL=WARNING",
                "tgbot:test",
            ]
        )
        .decode()
        .strip()
    )
    try:
        assert wait_for_log(cid, "bot_started")
    finally:
        subprocess.run(["docker", "rm", "-f", cid], check=True)


@pytest.mark.skipif(
    not Path("deploy/docker-compose.dev.yml").exists(),
    reason="no compose file",
)
def test_docker_compose_up(tmp_path):
    data = tmp_path / "data"
    env = os.environ.copy()
    env.update(
        {
            "BOT_TOKEN": "dummy",
            "ADMIN_CHAT_ID": "1",
            "LOG_LEVEL": "WARNING",
        }
    )
    subprocess.run(
        [
            "docker-compose",
            "-f",
            "deploy/docker-compose.dev.yml",
            "up",
            "-d",
            "--build",
        ],
        check=True,
        env=env,
    )
    try:
        cid = (
            subprocess.check_output(
                [
                    "docker-compose",
                    "-f",
                    "deploy/docker-compose.dev.yml",
                    "ps",
                    "-q",
                    "bot",
                ]
            )
            .decode()
            .strip()
        )
        for _ in range(20):
            out = subprocess.check_output(
                [
                    "docker",
                    "inspect",
                    cid,
                ]
            )
            state = json.loads(out)[0]["State"]
            status = state.get("Health", {}).get("Status")
            if status == "healthy":
                break
            time.sleep(1)
        else:
            raise AssertionError("container not healthy")
        assert data.exists()
    finally:
        subprocess.run(
            [
                "docker-compose",
                "-f",
                "deploy/docker-compose.dev.yml",
                "down",
                "-v",
            ],
            check=True,
            env=env,
        )
