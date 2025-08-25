import pytest
from datetime import datetime, UTC


def make_order(id, tier, zip_code, weight=1.0):
    return {
        "id": id,
        "external_id": id,
        "created_at": datetime.now(UTC),
        "buyer": {"name": "Test"},
        "destination": {"zip": zip_code, "city": "X", "state": "Y", "country": "US"},
        "items": [{"sku": "A", "name": "Item", "qty": 1, "weight": weight}],
        "shipping_tier": tier,
        "totals": {"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
    }


@pytest.mark.integration
def test_weight_and_free_rule(orders, order_model):
    order = order_model(**make_order("1", "Free", "99999"))
    orders.create_or_update(order)
    data = orders.get("1").model_dump()
    assert data["computed_weight"] == 1.5
    assert data["proposed_shipping_method"]["carrier"] == "UPS"


@pytest.mark.integration
def test_zip_override(orders, order_model):
    order = order_model(**make_order("2", "Free", "03224"))
    orders.create_or_update(order)
    data = orders.get("2").model_dump()
    assert data["proposed_shipping_method"]["carrier"] == "Home"


@pytest.mark.integration
def test_priority_zip_override(orders, order_model):
    order = order_model(**make_order("3", "Priority", "03224"))
    orders.create_or_update(order)
    data = orders.get("3").model_dump()
    assert data["proposed_shipping_method"]["carrier"] == "Home"
