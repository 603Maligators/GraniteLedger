from typing import Any, Dict
from forgecore.admin_api import HTTPException

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI

import os, sys, json, urllib.request
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
        oid = payload.get("order_id")
        url = os.getenv("VOLUSION_SYNC_URL")
        if url:
            data = json.dumps({"order_id": oid}).encode("utf-8")
            try:  # best effort network call
                urllib.request.urlopen(url, data=data, timeout=5)
            except Exception:
                pass
        self.ctx.event_bus.publish("volusion.sync", {"order_id": oid})

    def ingest_payload(self, item: Dict[str, Any]):
        data = normalize(item)
        order = self.OrderModel.model_validate(data)
        self.service.create_or_update(order, test=item.get("test") == True)
        return {"status": "ok", "id": order.id}

    def setup_routes(self, app: Any):
        @app.post("/gl/webhooks/volusion")
        def ingest(item: Dict[str, Any]):
            return self.ingest_payload(item)
