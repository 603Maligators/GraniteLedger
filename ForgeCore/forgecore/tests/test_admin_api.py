import os
import sys

import pytest

# Ensure the admin API uses the internal FastAPI stub for tests
import mini_fastapi
sys.modules["fastapi"] = mini_fastapi

from mini_fastapi.testclient import TestClient
from forgecore.runtime import ForgeRuntime
from forgecore.admin_api import create_app


@pytest.fixture
def runtime_client(tmp_path):
    mod_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
    mod_dir = os.path.abspath(mod_dir)
    rt = ForgeRuntime(mod_dir, storage_dir=str(tmp_path))
    rt.start()
    app = create_app(rt)
    client = TestClient(app)
    return rt, client


def test_api_modules_list_and_details(runtime_client):
    rt, client = runtime_client
    resp = client.get("/api/modules")
    assert resp.status_code == 200
    names = {m['name'] for m in resp.json()['modules']}
    assert names == {"basic_module", "rpg_inventory"}

    resp = client.get("/api/modules/basic_module")
    assert resp.json()['enabled'] is True
    rt.stop()


def test_api_storage_round_trip(runtime_client):
    rt, client = runtime_client
    resp = client.put("/api/storage/basic_module/foo", json={"value": {"x":1}})
    assert resp.status_code == 200
    resp = client.get("/api/storage/basic_module")
    assert resp.json()['keys'] == ['foo']
    resp = client.get("/api/storage/basic_module/foo")
    assert resp.json() == {"x":1}
    rt.stop()


def test_api_validate_returns_graph(runtime_client):
    rt, client = runtime_client
    resp = client.post("/api/validate")
    assert resp.status_code == 200
    graph = resp.json()['graph']
    assert 'rpg_inventory' in graph and 'basic_module' in graph
    rt.stop()
