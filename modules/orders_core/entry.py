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
        self.printing = None

    def on_enable(self):
        # replace automatic binding with service/model
        self.ctx.registry.unbind("orders.service@1.0", self)
        self.ctx.registry.bind("orders.service@1.0", self.service)
        self.ctx.registry.unbind("orders.models@1.0", self)
        self.ctx.registry.bind("orders.models@1.0", Order)
        self.printing = self.ctx.registry.get("printing.service@1.0")

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
            return order.model_dump()



        @app.post("/gl/orders/{oid}/status/{status}")
        def change_status(oid: str, status: str):
            try:
                order = self.service.change_status(oid, status)
            except ValueError as e:
                raise HTTPException(400)
            if not order:
                raise HTTPException(404)
            return order.model_dump()

        @app.post("/gl/orders/{oid}/addressed")
        def addressed(oid: str):
            order = self.service.get(oid)
            if not order:
                raise HTTPException(404)
            try:
                self.service.add_history(oid, "addressbook.added", "Address pushed to Apple Contacts (local record)")
                self.ctx.event_bus.publish("addressbook.added", {"order_id": oid, "detail": "added"})
                order = self.service.change_status(oid, "Addressed")
            except ValueError as e:
                raise HTTPException(400)
            return order.model_dump()

        @app.post("/gl/orders/batch/print/invoices")
        def batch_print_invoices(item: Dict[str, Any]):
            ids = item.get("ids", [])
            results = []
            for oid in ids:
                try:
                    res = self.printing.op_print_invoice(oid)
                    results.append({"id": oid, "ok": True, "detail": res.get("path")})
                except Exception as exc:  # pragma: no cover - error paths
                    results.append({"id": oid, "ok": False, "error": str(exc)})
            return {"results": results}

        @app.post("/gl/orders/batch/print/labels")
        def batch_print_labels(item: Dict[str, Any]):
            ids = item.get("ids", [])
            results = []
            for oid in ids:
                try:
                    res = self.printing.op_print_label(oid)
                    results.append({"id": oid, "ok": True, "detail": res.get("tracking")})
                except Exception as exc:  # pragma: no cover
                    results.append({"id": oid, "ok": False, "error": str(exc)})
            return {"results": results}

        @app.post("/gl/orders/batch/status")
        def batch_status(item: Dict[str, Any]):
            ids = item.get("ids", [])
            status = item.get("status")
            results = []
            for oid in ids:
                try:
                    order = self.service.change_status(oid, status)
                    if order:
                        results.append({"id": oid, "ok": True})
                    else:
                        results.append({"id": oid, "ok": False, "error": "not found"})
                except ValueError as e:
                    results.append({"id": oid, "ok": False, "error": str(e)})
            return {"results": results}

        self.app = app
