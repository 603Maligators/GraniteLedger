import pytest

from modules.shipping_rules.entry import ShippingRulesModule


@pytest.mark.unit
@pytest.mark.parametrize(
    "items,expected",
    [
        ([{"weight": 1.0, "qty": 2}], 2.5),
        ([], 0.5),
        ([{"weight": -1.0, "qty": 1}], -0.5),
    ],
)
def test_compute_weight(items, expected):
    mod = ShippingRulesModule()
    order = {"items": items}
    assert mod.compute_weight(order) == expected
