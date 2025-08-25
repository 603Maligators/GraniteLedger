import os
import random
import socket
from contextlib import contextmanager

import pytest

try:  # pragma: no cover
    from freezegun import freeze_time
except Exception:  # pragma: no cover
    freeze_time = None


@pytest.fixture(scope="session", autouse=True)
def _seed_rng():
    seed = int(os.environ.get("PYTEST_SEED", "12345"))
    random.seed(seed)
    return seed


@pytest.fixture
def temp_path(tmp_path_factory):
    return tmp_path_factory.mktemp("tmp")


@pytest.fixture
def frozen_time():
    if freeze_time is None:  # pragma: no cover
        pytest.skip("freezegun not installed")

    def freezer(timestr="2020-01-01"):
        return freeze_time(timestr)

    return freezer


@pytest.fixture
def set_env(monkeypatch):
    def setter(key: str, value: str):
        monkeypatch.setenv(key, value)
    return setter


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    if os.environ.get("ALLOW_NET") == "1":
        return
    def guard(*args, **kwargs):  # type: ignore[unused-arg]
        raise RuntimeError("Network access disabled during tests")
    monkeypatch.setattr(socket.socket, "connect", guard)


def pytest_runtest_setup(item):
    if "slow" in item.keywords and os.environ.get("RUN_SLOW") != "1":
        pytest.skip("need RUN_SLOW=1 to run")
