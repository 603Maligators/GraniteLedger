import shutil
import os
import pytest
import sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE)
sys.path.append(os.path.join(BASE, "ForgeCore"))

from forgecore.runtime import create_runtime


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
