from datetime import datetime


def make_order(id):
    return {
        "id": id,
        "external_id": id,
        "created_at": datetime.utcnow(),
        "buyer": {"name": "P"},
        "destination": {"zip": "99999", "city": "X", "state": "Y", "country": "US"},
        "items": [{"sku": "A", "name": "Item", "qty": 1, "weight": 1.0}],
        "shipping_tier": "Free",
        "totals": {"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
    }


def test_reprint_and_void(printing, orders, order_model, events):
    order = order_model(**make_order("p1"))
    orders.create_or_update(order)
    printing.op_print_invoice("p1")
    assert orders.get("p1").status == "Printed"
    printing.op_reprint_invoice("p1")
    assert orders.get("p1").status == "Printed"
    # approve and ship
    method = orders.get("p1").proposed_shipping_method
    orders.update("p1", {"approved_shipping_method": method})
    orders.change_status("p1", "Addressed")
    orders.change_status("p1", "Bags Pulled")
    orders.change_status("p1", "Ship Method Chosen")
    res = printing.op_print_label("p1")
    status_after = orders.get("p1").status
    assert status_after == "Shipped"
    first_tracking = res["tracking"]
    printing.op_reprint_label("p1")
    assert orders.get("p1").status == "Shipped"
    res2 = printing.op_void_rebuy("p1")
    assert res2["tracking"] != first_tracking
    assert orders.get("p1").status == "Shipped"
    topics = [e["topic"] for e in events.list_events()]
    assert "order.label.voided" in topics and topics.count("order.label.purchased") == 2
