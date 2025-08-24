from typing import Any, Dict, List
from forgecore.admin_api import HTTPException
try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI

import os, sys
sys.path.append(os.path.dirname(__file__))
from service import OrderService
from models import Order


class OrdersCoreModule:
    def on_load(self, ctx):
        self.ctx = ctx
        self.service = OrderService(ctx)

    def on_enable(self):
        # replace automatic binding with service/model
        self.ctx.registry.unbind("orders.service@1.0", self)
        self.ctx.registry.bind("orders.service@1.0", self.service)
        self.ctx.registry.unbind("orders.models@1.0", self)
        self.ctx.registry.bind("orders.models@1.0", Order)

    # routes -------------------------------------------------------------
    def setup_routes(self, app: Any):
        @app.get("/gl/orders")
        def list_orders():
            return [o.model_dump() for o in self.service.list_orders()]

        @app.get("/gl/orders/{oid}")
        def get_order(oid: str):
            order = self.service.get(oid)
            if not order:
                raise HTTPException(404)
            return order.model_dump()

        @app.post("/gl/orders")
        def create_order(item: Dict[str, Any]):
            order = Order.model_validate(item)
            self.service.create_or_update(order)
            fresh = self.service.get(order.id)
            return fresh.model_dump() if fresh else order.model_dump()

        @app.patch("/gl/orders/{oid}")
        def update_order(oid: str, item: Dict[str, Any]):
            order = self.service.update(oid, item)
            if not order:
                raise HTTPException(404)
            return order.model_dump()

        def _extract_ids(payload):
            if isinstance(payload, dict):
                return payload.get("ids", [])
            return payload

        @app.post("/gl/orders/batch/print/invoices")
        def batch_print_invoices(payload: Any):
            ids = _extract_ids(payload)
            printing = self.ctx.registry.get("printing.service@1.0")
            return [printing.op_print_invoice(i) for i in ids]

        @app.post("/gl/orders/batch/print/labels")
        def batch_print_labels(payload: Any):
            ids = _extract_ids(payload)
            printing = self.ctx.registry.get("printing.service@1.0")
            return [printing.op_print_label(i) for i in ids]

        @app.post("/gl/orders/batch/status/{status}")
        def batch_status(status: str, payload: Any):
            ids = _extract_ids(payload)
            out = []
            for oid in ids:
                try:
                    order = self.service.change_status(oid, status)
                except ValueError:
                    order = None
                out.append(order.model_dump() if order else None)
            return out

        @app.post("/gl/orders/{oid}/status/{status}")
        def change_status(oid: str, status: str):
            try:
                order = self.service.change_status(oid, status)
            except ValueError:
                raise HTTPException(400)
            if not order:
                raise HTTPException(404)
            return order.model_dump()

        @app.post("/gl/orders/{oid}/addressed")
        def mark_addressed(oid: str):
            try:
                order = self.service.change_status(oid, "Addressed")
            except ValueError:
                raise HTTPException(400)
            if not order:
                raise HTTPException(404)
            self.ctx.event_bus.publish(
                "addressbook.added", {"order_id": oid, "detail": "Apple Contacts (local)"}
            )
            return order.model_dump()

        self.app = app
