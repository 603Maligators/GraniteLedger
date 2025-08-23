from datetime import datetime


def make_order(id):
    return {
        "id": id,
        "external_id": id,
        "created_at": datetime.utcnow(),
        "buyer": {"name": "Batch"},
        "destination": {"zip": "99990", "city": "X", "state": "Y", "country": "US"},
        "items": [{"sku": "A", "name": "Item", "qty": 1, "weight": 1.0}],
        "shipping_tier": "Free",
        "totals": {"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
    }


def test_batch_ops(orders_api, orders, order_model, runtime):
    o1 = order_model(**make_order("b1"))
    o2 = order_model(**make_order("b2"))
    orders.create_or_update(o1)
    orders.create_or_update(o2)
    # helpers
    def call(path, payload):
        func = next(r for r in orders_api.routes if r.path == path).endpoint
        return func(payload)

    data = call("/gl/orders/batch/print/invoices", {"ids": ["b1", "b2"]})
    assert "b1" in data and "b2" in data
    # prepare for label on b1
    printing_method = orders.get("b1").proposed_shipping_method
    orders.update("b1", {"approved_shipping_method": printing_method})
    runtime.event_bus.publish("order.shipping.approved", {"order_id": "b1", "method": printing_method})
    orders.change_status("b1", "Addressed")
    orders.change_status("b1", "Bags Pulled")
    orders.change_status("b1", "Ship Method Chosen")
    # batch print labels (b1 ok, b2 fails)
    data = call("/gl/orders/batch/print/labels", {"ids": ["b1", "b2"]})
    assert "tracking" in data["b1"]
    assert "error" in data["b2"]
    # batch status advance both to Completed (b2 should error due to flow)
    result = call(
        "/gl/orders/batch/status", {"ids": ["b1", "b2"], "status": "Completed"}
    )
    assert result["b1"]["ok"] is True
    assert "error" in result["b2"]
