import pytest

pytest.importorskip("pytest_benchmark")

from modules.volusion_webhook.normalizer import normalize


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload",
    [
        {"id": 1, "items": []},
        {},
        {"nested": {"a": [1, 2, 3]}, "value": "x"},
    ],
)
def test_normalize_returns_payload(payload):
    assert normalize(payload) == payload


@pytest.mark.unit
def test_normalize_benchmark(benchmark):
    payload = {"foo": "bar", "nums": list(range(100))}
    result = benchmark(normalize, payload)
    assert result == payload
