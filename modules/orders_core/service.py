from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
import os, sys
sys.path.append(os.path.dirname(__file__))
from models import Order


ALLOWED_STATUS = [
    "New",
    "Printed",
    "Addressed",
    "Bags Pulled",
    "Ship Method Chosen",
    "Shipped",
    "Completed",
]

STATUS_FLOW = {
    "New": ["Printed"],
    "Printed": ["Addressed"],
    "Addressed": ["Bags Pulled"],
    "Bags Pulled": ["Ship Method Chosen"],
    "Ship Method Chosen": ["Shipped"],
    "Shipped": ["Completed"],
    "Completed": [],
}


class OrderService:
    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.storage = ctx.storage
        self.event_bus = ctx.event_bus
        self.module_name = ctx.manifest["name"]
        self.index: List[str] = self.storage.load(self.module_name, "index", [])
        self.external: Dict[str, str] = self.storage.load(self.module_name, "external_ids", {})

    # persistence helpers
    def _save_index(self):
        self.storage.store(self.module_name, "index", self.index)
        self.storage.store(self.module_name, "external_ids", self.external)

    def _store_order(self, order: Order):
        self.storage.store(self.module_name, f"order_{order.id}", order.model_dump(mode="json"))
        if order.id not in self.index:
            self.index.append(order.id)
            self._save_index()

    def _load_order(self, oid: str) -> Optional[Order]:
        data = self.storage.load(self.module_name, f"order_{oid}")
        if not data:
            return None
        return Order.parse_obj(data)

    # public API
    def list_orders(self) -> List[Order]:
        return [self._load_order(i) for i in self.index if self._load_order(i)]

    def get(self, oid: str) -> Optional[Order]:
        return self._load_order(oid)

    def create_or_update(self, order: Order, test: bool = False) -> Order:
        if order.external_id and order.external_id in self.external:
            existing = self._load_order(self.external[order.external_id])
            if existing:
                # merge basic fields, keep status etc
                order.id = existing.id
                order.status = existing.status
                order.history = existing.history
        else:
            self.external[order.external_id] = order.id if order.external_id else order.id
        order.history.append({
            "ts": datetime.utcnow(),
            "event": "order.received",
            "detail": "test" if test else "received",
        })
        self._store_order(order)
        payload = {"order_id": order.id, "order": order.model_dump(mode="json"), "test": test}
        self.event_bus.publish("order.received", payload)
        return order

    def update(self, oid: str, data: Dict) -> Optional[Order]:
        order = self._load_order(oid)
        if not order:
            return None
        for k, v in data.items():
            setattr(order, k, v)
        order.history.append({
            "ts": datetime.utcnow(),
            "event": "order.updated",
            "detail": "updated",
        })
        self._store_order(order)
        self.event_bus.publish("order.updated", {"order_id": oid, "order": order.model_dump(mode="json")})
        return order

    def change_status(self, oid: str, new_status: str) -> Optional[Order]:
        order = self._load_order(oid)
        if not order:
            return None
        if new_status not in ALLOWED_STATUS:
            raise ValueError("unknown status")
        if new_status not in STATUS_FLOW.get(order.status, []):
            raise ValueError("illegal transition")
        order.status = new_status
        order.history.append({
            "ts": datetime.utcnow(),
            "event": "order.status.changed",
            "detail": new_status,
        })
        self._store_order(order)
        self.event_bus.publish("order.status.changed", {"order_id": oid, "status": new_status})
        if new_status == "Completed":
            self.event_bus.publish("order.completed", {"order_id": oid})
        return order

