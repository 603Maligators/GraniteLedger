import pytest

hypothesis = pytest.importorskip("hypothesis")
st = hypothesis.strategies

from modules.volusion_webhook.normalizer import normalize


@hypothesis.given(st.dictionaries(keys=st.text(), values=st.integers()))
@pytest.mark.property
def test_normalize_idempotent(payload):
    assert normalize(normalize(payload)) == payload
