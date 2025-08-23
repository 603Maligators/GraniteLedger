from datetime import datetime


def make_order(id):
    return {
        "id": id,
        "external_id": id,
        "created_at": datetime.utcnow(),
        "buyer": {"name": "Print"},
        "destination": {"zip": "99990", "city": "X", "state": "Y", "country": "US"},
        "items": [{"sku": "A", "name": "Item", "qty": 1, "weight": 1.0}],
        "shipping_tier": "Free",
        "totals": {"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
    }


def test_reprint_and_void(orders, order_model, printing, events, runtime):
    order = order_model(**make_order("p1"))
    orders.create_or_update(order)
    printing.op_print_invoice("p1")
    orders.change_status("p1", "Addressed")
    orders.change_status("p1", "Bags Pulled")
    method = orders.get("p1").proposed_shipping_method
    orders.update("p1", {"approved_shipping_method": method})
    runtime.event_bus.publish("order.shipping.approved", {"order_id": "p1", "method": method})
    orders.change_status("p1", "Ship Method Chosen")
    printing.op_print_label("p1")
    tracking1 = orders.get("p1").tracking_number
    # reprints
    printing.op_reprint_invoice("p1")
    printing.op_reprint_label("p1")
    # void and rebuy
    printing.op_void_rebuy("p1")
    tracking2 = orders.get("p1").tracking_number
    assert tracking1 != tracking2
    assert orders.get("p1").status == "Shipped"
    topics = [e["topic"] for e in events.list_events()]
    assert "order.label.voided" in topics
    assert topics.count("order.invoice.printed") >= 2
    assert topics.count("order.label.printed") >= 2
