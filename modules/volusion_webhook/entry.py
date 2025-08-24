from typing import Any, Dict
from forgecore.admin_api import HTTPException
import os
import json
from urllib import request as urlrequest

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI

import sys
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
        if not url:
            self.ctx.event_bus.publish("volusion.sync.skipped", {"order_id": oid})
            return
        try:
            data = json.dumps({"order_id": oid}).encode()
            req = urlrequest.Request(url, data=data, headers={"Content-Type": "application/json"})
            urlrequest.urlopen(req, timeout=5)  # nosec - demo
            self.ctx.event_bus.publish("volusion.sync", {"order_id": oid, "url": url})
        except Exception as exc:  # pragma: no cover
            self.ctx.event_bus.publish("volusion.sync.error", {"order_id": oid, "detail": str(exc)})

    def ingest_payload(self, item: Dict[str, Any], test_flag: bool = False):
        data = normalize(item)
        order = self.OrderModel.model_validate(data)
        self.service.create_or_update(order, test=test_flag)
        return {"status": "ok", "id": order.id}

    def setup_routes(self, app: Any):
        @app.post("/gl/webhooks/volusion")
        def ingest(item: Dict[str, Any], request=None):
            test_flag = False
            if request:
                hdr = request.headers.get("X-GL-Test") if hasattr(request, "headers") else None
                test_flag = hdr == "1"
            return self.ingest_payload(item, test_flag=test_flag)
