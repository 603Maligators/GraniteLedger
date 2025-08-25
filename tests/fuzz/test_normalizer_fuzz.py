import pytest

hypothesis = pytest.importorskip("hypothesis")
st = hypothesis.strategies

from modules.volusion_webhook.normalizer import normalize


@hypothesis.given(
    st.recursive(
        st.none() | st.booleans() | st.integers() | st.text(),
        lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    )
)
@pytest.mark.fuzz
def test_normalize_handles_arbitrary_payload(payload):
    normalize(payload)
