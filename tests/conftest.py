import os
import pytest
import sys
import shutil
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE)
sys.path.append(os.path.join(BASE, "ForgeCore"))

from forgecore.runtime import create_runtime
try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI  # type: ignore


@pytest.fixture
def runtime():
    shutil.rmtree("modules/_storage", ignore_errors=True)
    rt = create_runtime("modules")
    rt.start()
    yield rt
    shutil.rmtree("modules/_storage", ignore_errors=True)


@pytest.fixture
def orders(runtime):
    return runtime.registry.get("orders.service@1.0")


@pytest.fixture
def printing(runtime):
    return runtime.registry.get("printing.service@1.0")


@pytest.fixture
def events(runtime):
    return runtime.registry.get("events.log@1.0")


@pytest.fixture
def order_model(runtime):
    return runtime.registry.get("orders.models@1.0")


@pytest.fixture
def volusion(runtime):
    return runtime.registry.get("webhooks.volusion@1.0")


@pytest.fixture
def orders_api(runtime):
    class Dummy:
        def __init__(self):
            self.routes = []

        def get(self, path, **kwargs):
            def deco(fn):
                self.routes.append(type("R", (), {"path": path, "endpoint": fn}))
                return fn
            return deco

        def post(self, path, **kwargs):
            return self.get(path, **kwargs)

        def patch(self, path, **kwargs):
            return self.get(path, **kwargs)

    app = Dummy()
    mod = runtime.loader.modules["orders_core"].instance
    mod.setup_routes(app)
    return app
