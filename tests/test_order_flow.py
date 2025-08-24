from datetime import datetime


def order_payload(id):
    return {
        "id": id,
        "created_at": datetime.utcnow(),
        "buyer": {"name": "Flow"},
        "destination": {"zip": "99999", "city": "X", "state": "Y", "country": "US"},
        "items": [{"sku": "A", "name": "Item", "qty": 1, "weight": 1.0}],
        "shipping_tier": "Free",
        "totals": {"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
    }


def test_happy_flow(runtime, volusion, events):
    volusion.ingest_payload(order_payload("o1"))
    # print invoice
    runtime.app.handle("POST", "/gl/orders/o1/print/invoice")
    runtime.app.handle("POST", "/gl/orders/o1/addressed")
    orders = runtime.registry.get("orders.service@1.0")
    orders.change_status("o1", "Bags Pulled")
    runtime.app.handle("POST", "/gl/orders/o1/shipping/approve")
    runtime.app.handle("POST", "/gl/orders/o1/print/label")
    orders.change_status("o1", "Completed")
    order = runtime.registry.get("orders.service@1.0").get("o1").model_dump()
    assert order["status"] == "Completed"
    assert order["approved_shipping_method"] is not None
    assert order["tracking_number"].startswith("GL-o1-")
    topics = [e["topic"] for e in events.list_events()]
    expected = [
        "order.received",
        "order.shipping.selected",
        "order.invoice.printed",
        "addressbook.added",
        "order.shipping.approved",
        "order.label.purchased",
        "order.label.printed",
        "order.completed",
    ]
    pos = 0
    for t in expected:
        assert t in topics[pos:]
        pos = topics.index(t, pos) + 1
