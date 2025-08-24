from datetime import datetime


def make_order(id):
    return {
        "id": id,
        "external_id": id,
        "created_at": datetime.utcnow(),
        "buyer": {"name": "B"},
        "destination": {"zip": "99999", "city": "X", "state": "Y", "country": "US"},
        "items": [{"sku": "A", "name": "Item", "qty": 1, "weight": 1.0}],
        "shipping_tier": "Free",
        "totals": {"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
    }


def test_batch_ops(runtime, orders, order_model):
    a = order_model(**make_order("a"))
    b = order_model(**make_order("b"))
    orders.create_or_update(a)
    orders.create_or_update(b)
    # invoices
    resp = runtime.app.handle("POST", "/gl/orders/batch/print/invoices", json={"ids": ["a", "b"]})
    assert all(r["ok"] for r in resp["results"])
    # prepare for labels
    for oid in ["a", "b"]:
        orders.update(oid, {"approved_shipping_method": {"carrier": "USPS", "service": "Ground", "cost": 5.0, "eta_days": 5}})
        orders.change_status(oid, "Addressed")
        orders.change_status(oid, "Bags Pulled")
        orders.change_status(oid, "Ship Method Chosen")
    resp = runtime.app.handle("POST", "/gl/orders/batch/print/labels", json={"ids": ["a", "b"]})
    assert all(r["ok"] for r in resp["results"])
    resp = runtime.app.handle(
        "POST", "/gl/orders/batch/status", json={"ids": ["a", "ghost"], "status": "Completed"}
    )
    results = {r["id"]: r for r in resp["results"]}
    assert results["a"]["ok"] is True and results["ghost"]["ok"] is False
