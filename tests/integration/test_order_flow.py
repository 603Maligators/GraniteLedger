import pytest
from datetime import datetime, UTC


def make_order(id):
    return {
        "id": id,
        "external_id": id,
        "created_at": datetime.now(UTC),
        "buyer": {"name": "Flow"},
        "destination": {"zip": "99999", "city": "X", "state": "Y", "country": "US"},
        "items": [{"sku": "A", "name": "Item", "qty": 1, "weight": 1.0}],
        "shipping_tier": "Free",
        "totals": {"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
    }


@pytest.mark.integration
def test_full_flow(orders, order_model, printing, events, runtime):
    order = order_model(**make_order("x1"))
    orders.create_or_update(order)
    # print invoice
    printing.op_print_invoice("x1")
    orders.change_status("x1", "Addressed")
    orders.change_status("x1", "Bags Pulled")
    # approve shipping
    method = orders.get("x1").proposed_shipping_method
    orders.update("x1", {"approved_shipping_method": method})
    runtime.event_bus.publish("order.shipping.approved", {"order_id": "x1", "method": method})
    orders.change_status("x1", "Ship Method Chosen")
    # print label
    printing.op_print_label("x1")
    orders.change_status("x1", "Completed")
    data = orders.get("x1").model_dump()
    assert data["status"] == "Completed"
    assert data["tracking_number"] is not None
    topics = [e["topic"] for e in events.list_events()]
    for t in ["order.received", "order.invoice.printed", "order.label.printed", "order.completed"]:
        assert t in topics
