import uuid
from typing import Any
from datetime import datetime, UTC
from forgecore.admin_api import HTTPException

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI


class TestKitsModule:
    def on_load(self, ctx):
        self.ctx = ctx
        self.orders = ctx.registry.get("orders.service@1.0")
        self.printing = ctx.registry.get("printing.service@1.0")
        self.OrderModel = ctx.registry.get("orders.models@1.0")
        ctx.registry.bind("tests.kit@1.0", self)

    def setup_routes(self, app: Any):
        @app.post("/gl/test/order")
        def test_order():
            oid = str(uuid.uuid4())
            order = self.OrderModel(
                id=oid,
                external_id=oid,
                created_at=datetime.now(UTC),
                buyer={"name": "Test Buyer"},
                destination={"zip": "99999", "city": "X", "state": "YY", "country": "US"},
                items=[{"sku": "SKU1", "name": "Item", "qty": 1, "weight": 1.0}],
                shipping_tier="Free",
                totals={"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
            )
            self.orders.create_or_update(order, test=True)
            return {"id": oid}

        @app.post("/gl/test/print")
        def test_print():
            orders = self.orders.list_orders()
            if not orders:
                raise HTTPException(404)
            oid = orders[-1].id
            self.printing.op_print_invoice(oid, test=True)
            return {"id": oid}

        @app.post("/gl/test/ship")
        def test_ship():
            orders = self.orders.list_orders()
            if not orders:
                raise HTTPException(404)
            oid = orders[-1].id
            self.orders.update(
                oid,
                {
                    "approved_shipping_method": {
                        "carrier": "USPS",
                        "service": "Ground",
                        "cost": 5.0,
                        "eta_days": 5,
                    }
                },
            )
            self.printing.op_print_label(oid, test=True)
            return {"id": oid}
