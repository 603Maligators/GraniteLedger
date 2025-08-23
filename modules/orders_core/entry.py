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

        self.app = app
