from datetime import datetime
from typing import Any
from forgecore.admin_api import HTTPException

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI

EVENT_TOPICS = [
    "order.received",
    "order.updated",
    "order.status.changed",
    "order.shipping.selected",
    "order.shipping.approved",
    "order.invoice.printed",
    "order.label.purchased",
    "order.label.printed",
    "order.label.voided",
    "order.completed",
    "addressbook.added",
    "volusion.sync",
    "volusion.sync.skipped",
    "volusion.sync.error",
]


class EventsLogModule:
    def on_load(self, ctx):
        self.ctx = ctx
        self.module_name = ctx.manifest["name"]
        self.events = ctx.storage.load(self.module_name, "events", [])
        for topic in EVENT_TOPICS:
            ctx.event_bus.subscribe(topic, lambda payload, t=topic: self._handle(t, payload))
        ctx.registry.bind("events.log@1.0", self)

    def _handle(self, topic: str, payload: Any):
        rec = {
            "ts": datetime.utcnow().isoformat(),
            "topic": topic,
            "order_id": payload.get("order_id"),
            "detail": payload.get("detail"),
            "rationale": payload.get("rationale"),
            "test": payload.get("test", False),
        }
        self.events.append(rec)
        self.ctx.storage.store(self.module_name, "events", self.events)

    def list_events(self):
        return list(self.events)

    def setup_routes(self, app: Any):
        @app.get("/gl/logs")
        def get_logs(topic: str | None = None, order_id: str | None = None, q: str | None = None, since: str | None = None):
            events = self.list_events()
            if topic:
                events = [e for e in events if e.get("topic", "").startswith(topic)]
            if order_id:
                events = [e for e in events if e.get("order_id") == order_id]
            if q:
                events = [
                    e
                    for e in events
                    if q.lower() in str(e.get("detail", "")).lower()
                    or q.lower() in str(e.get("rationale", "")).lower()
                ]
            if since:
                try:
                    cutoff = datetime.fromisoformat(since)
                    events = [e for e in events if datetime.fromisoformat(e["ts"]) > cutoff]
                except ValueError:
                    raise HTTPException(400)
            events.sort(key=lambda e: e["ts"], reverse=True)
            return events
