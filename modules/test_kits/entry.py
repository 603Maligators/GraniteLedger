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
        ctx.registry.bind("tests.kit@1.0", self)

    def _orders_service(self):
        return self.ctx.registry.get("orders.service@1.0")

    def _printing_service(self):
        return self.ctx.registry.get("printing.service@1.0")

    def _order_model(self):
        return self.ctx.registry.get("orders.models@1.0")

    def setup_routes(self, app: Any):
        @app.post("/gl/test/order")
        def test_order():
            oid = str(uuid.uuid4())
            Order = self._order_model()
            order = Order(
                id=oid,
                external_id=oid,
                created_at=datetime.now(UTC),
                buyer={"name": "Test Buyer"},
                destination={"zip": "99999", "city": "X", "state": "YY", "country": "US"},
                items=[{"sku": "SKU1", "name": "Item", "qty": 1, "weight": 1.0}],
                shipping_tier="Free",
                totals={"subtotal": 10.0, "shipping": 0.0, "tax": 0.0, "grand_total": 10.0},
            )
            self._orders_service().create_or_update(order, test=True)
            return {"id": oid}

        @app.post("/gl/test/print")
        def test_print():
            orders = self._orders_service().list_orders()
            if not orders:
                raise HTTPException(404)
            oid = orders[-1].id
            self._printing_service().op_print_invoice(oid, test=True)
            return {"id": oid}

        @app.post("/gl/test/ship")
        def test_ship():
            orders = self._orders_service().list_orders()
            if not orders:
                raise HTTPException(404)
            oid = orders[-1].id
            self._orders_service().update(
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
            self._printing_service().op_print_label(oid, test=True)
            return {"id": oid}
