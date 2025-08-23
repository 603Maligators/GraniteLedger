from datetime import datetime
from typing import Any

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
            "test": payload.get("test", False),
        }
        self.events.append(rec)
        self.ctx.storage.store(self.module_name, "events", self.events)

    def list_events(self, topic: str | None = None, q: str | None = None, since: str | None = None):
        evs = list(self.events)
        if topic:
            evs = [e for e in evs if e["topic"].startswith(topic)]
        if q:
            evs = [e for e in evs if q.lower() in (e.get("detail") or "").lower()]
        if since:
            try:
                dt = datetime.fromisoformat(since)
                evs = [e for e in evs if datetime.fromisoformat(e["ts"]) >= dt]
            except Exception:  # pragma: no cover
                pass
        evs.sort(key=lambda e: e["ts"], reverse=True)
        return evs

    def setup_routes(self, app: Any):
        @app.get("/gl/logs")
        def get_logs(topic: str = "", q: str = "", since: str = ""):
            return self.list_events(topic or None, q or None, since or None)
