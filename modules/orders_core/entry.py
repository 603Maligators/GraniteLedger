from typing import Any, Dict
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
        # optional access to printing service for batch ops
        try:
            self.printing = self.ctx.registry.get("printing.service@1.0")
        except Exception:  # pragma: no cover
            self.printing = None

    # routes -------------------------------------------------------------
    def setup_routes(self, app: Any):
        @app.get("/gl/orders")
        def list_orders():
            return [o.dict() for o in self.service.list_orders()]

        @app.get("/gl/orders/{oid}")
        def get_order(oid: str):
            order = self.service.get(oid)
            if not order:
                raise HTTPException(404)
            return order.dict()

        @app.post("/gl/orders")
        def create_order(item: Dict[str, Any]):
            order = Order.parse_obj(item)
            self.service.create_or_update(order)
            return order.dict()

        @app.patch("/gl/orders/{oid}")
        def update_order(oid: str, item: Dict[str, Any]):
            order = self.service.update(oid, item)
            if not order:
                raise HTTPException(404)
            return order.dict()

        @app.post("/gl/orders/{oid}/status/{status}")
        def change_status(oid: str, status: str):
            try:
                order = self.service.change_status(oid, status)
            except ValueError:
                raise HTTPException(400)
            if not order:
                raise HTTPException(404)
            return order.dict()

        @app.post("/gl/orders/{oid}/addressed")
        def addressed(oid: str):
            try:
                order = self.service.change_status(oid, "Addressed")
            except ValueError:
                raise HTTPException(400)
            if not order:
                raise HTTPException(404)
            self.service.append_history(
                oid, "addressbook.added", "Address pushed to Apple Contacts (stub)"
            )
            self.ctx.event_bus.publish("addressbook.added", {"order_id": oid})
            return self.service.get(oid).dict()

        @app.post("/gl/orders/batch/print/invoices")
        def batch_print_invoices(ids: Dict[str, Any]):
            if not self.printing:
                raise HTTPException(500, "printing service unavailable")
            results = {}
            for oid in ids.get("ids", []):
                try:
                    results[oid] = self.printing.op_print_invoice(oid)
                except Exception as e:  # pragma: no cover
                    results[oid] = {"error": str(e)}
            return results

            
        @app.post("/gl/orders/batch/print/labels")
        def batch_print_labels(ids: Dict[str, Any]):
            if not self.printing:
                raise HTTPException(500, "printing service unavailable")
            results = {}
            for oid in ids.get("ids", []):
                try:
                    results[oid] = self.printing.op_print_label(oid)
                except Exception as e:  # pragma: no cover
                    results[oid] = {"error": str(e)}
            return results

        @app.post("/gl/orders/batch/status")
        def batch_status(payload: Dict[str, Any]):
            status = payload.get("status")
            results = {}
            for oid in payload.get("ids", []):
                try:
                    order = self.service.change_status(oid, status)
                    if not order:
                        raise ValueError("not found")
                    results[oid] = {"ok": True}
                except Exception as e:
                    results[oid] = {"error": str(e)}
            return results

        self.app = app
