from datetime import datetime, timezone

import pytest
from forgecore.admin_api import HTTPException


def make_order(id):
    return {
        "id": id,
        "external_id": id,
        "created_at": datetime.now(timezone.utc),
        "buyer": {"name": "T"},
        "destination": {"zip": "99999", "city": "X", "state": "Y", "country": "US"},
        "items": [{"sku": "A", "name": "Item", "qty": 1, "weight": 1.0}],
        "shipping_tier": "Free",
        "totals": {"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
    }


class DummyApp:
    def __init__(self):
        self.routes = {}

    def get(self, path):
        def dec(fn):
            self.routes[("GET", path)] = fn
            return fn
        return dec

    def post(self, path):
        def dec(fn):
            self.routes[("POST", path)] = fn
            return fn
        return dec

    def patch(self, path):
        def dec(fn):
            self.routes[("PATCH", path)] = fn
            return fn
        return dec


def test_negative_weight_rejected(order_model):
    from pydantic import ValidationError
    bad = make_order("neg")
    bad["items"][0]["weight"] = -1
    with pytest.raises(ValidationError):
        order_model(**bad)


def test_missing_buyer_returns_422(runtime):
    orders_module = runtime.loader.modules["orders_core"].instance
    app = DummyApp()
    orders_module.setup_routes(app)
    create = app.routes[("POST", "/gl/orders")]
    bad = make_order("bad")
    bad.pop("buyer")
    with pytest.raises(HTTPException) as exc:
        create(bad)
    assert exc.value.status_code == 422


def test_logs_since_timezone(runtime, orders, order_model):
    events_module = runtime.loader.modules["events_log"].instance
    app = DummyApp()
    events_module.setup_routes(app)
    get_logs = app.routes[("GET", "/gl/logs")]
    since = datetime.now(timezone.utc).isoformat()
    orders.create_or_update(order_model(**make_order("tz")))
    logs = get_logs(topic="order.", since=since)
    assert any(e["topic"] == "order.received" for e in logs)


def test_approve_shipping_early_conflict(runtime, orders, order_model):
    shipping_module = runtime.loader.modules["shipping_rules"].instance
    app = DummyApp()
    shipping_module.setup_routes(app)
    approve = app.routes[("POST", "/gl/orders/{oid}/shipping/approve")]
    orders.create_or_update(order_model(**make_order("early")))
    with pytest.raises(HTTPException) as exc:
        approve("early")
    assert exc.value.status_code == 409
