from datetime import datetime, UTC

payload = {
    "id": "ext1",
    "created_at": datetime.now(UTC),
    "buyer": {"name": "Webhook"},
    "destination": {"zip": "99999", "city": "X", "state": "Y", "country": "US"},
    "items": [{"sku": "A", "name": "Item", "qty": 1, "weight": 1.0}],
    "shipping_tier": "Free",
    "totals": {"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
}


def test_idempotent_webhook(volusion, orders):
    volusion.ingest_payload(payload)
    volusion.ingest_payload(payload)
    assert len(orders.list_orders()) == 1
