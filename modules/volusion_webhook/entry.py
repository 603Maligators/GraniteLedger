from typing import Any, Dict
from forgecore.admin_api import HTTPException

try:
    from fastapi import FastAPI, Header
except Exception:  # pragma: no cover
    from mini_fastapi import FastAPI  # type: ignore
    Header = lambda default=0: default  # type: ignore

import os, sys
sys.path.append(os.path.dirname(__file__))
from normalizer import normalize


class VolusionWebhookModule:
    def on_load(self, ctx):
        self.ctx = ctx
        self.service = None
        self.OrderModel = None
        ctx.event_bus.subscribe("order.completed", self.on_completed)
        ctx.registry.bind("webhooks.volusion@1.0", self)

    def on_enable(self):
        self.service = self.ctx.registry.get("orders.service@1.0")
        self.OrderModel = self.ctx.registry.get("orders.models@1.0")

    def on_completed(self, payload: Dict[str, Any]):
        # stub callback
        self.ctx.event_bus.publish(
            "volusion.sync", {"order_id": payload.get("order_id")}
        )

    def ingest_payload(self, item: Dict[str, Any]):
        data = normalize(item)
        order = self.OrderModel.parse_obj(data)
        self.service.create_or_update(order, test=item.get("test") == True)
        return {"status": "ok", "id": order.id}

    def setup_routes(self, app: Any):
        @app.post("/gl/webhooks/volusion")
        def ingest(item: Dict[str, Any], gl_test: int = Header(0)):
            if gl_test == 1:
                item["test"] = True
            return self.ingest_payload(item)
