from typing import Any, Dict, List
from datetime import datetime
from forgecore.admin_api import HTTPException

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI


class ShippingRulesModule:
    def on_load(self, ctx):
        self.ctx = ctx
        self.service = None
        ctx.event_bus.subscribe("order.received", self.handle)
        ctx.event_bus.subscribe("order.updated", self.handle)
        ctx.registry.bind("shipping.rules@1.0", self)

    def on_enable(self):
        self.service = self.ctx.registry.get("orders.service@1.0")

    # shipping logic -----------------------------------------------------
    def compute_weight(self, order: Dict) -> float:
        total = 0.0
        for it in order.get("items", []):
            total += it.get("weight", 0) * it.get("qty", 1)
        return round(total + 0.5, 2)

    def shipping_options(self, order: Dict) -> List[Dict]:
        weight = self.compute_weight(order)
        base = 5.0 + weight * 0.1
        last = int(order["destination"]["zip"][-1])
        diff = (last % 5) / 10.0
        cheapest = {"carrier": "USPS", "service": "Ground", "cost": round(base, 2), "eta_days": 5}
        candidate = {
            "carrier": "UPS",
            "service": "Ground",
            "cost": round(base + diff + 0.1, 2),
            "eta_days": 3,
        }
        priority = {
            "carrier": "USPS",
            "service": "Priority",
            "cost": round(base + 3, 2),
            "eta_days": 2,
        }
        home = {
            "carrier": "Home",
            "service": "Delivery",
            "cost": round(base + 2, 2),
            "eta_days": 4,
        }
        return [cheapest, candidate, priority, home]

    def choose_method(self, order: Dict) -> Dict:
        zip_code = order["destination"]["zip"]
        tier = order.get("shipping_tier")
        options = self.shipping_options(order)
        # ZIP override always home delivery
        if zip_code == "03224":
            chosen = options[3]
            chosen = dict(chosen)
            chosen["rationale"] = "zip override"
            return chosen
        if tier == "Priority":
            chosen = options[2]
            chosen = dict(chosen)
            chosen["rationale"] = "priority"
            return chosen
        if tier == "Free":
            opts = sorted(options[:2], key=lambda o: o["cost"])
            cheapest, candidate = opts
            if (candidate["cost"] - cheapest["cost"] < 0.3) and (candidate["eta_days"] < cheapest["eta_days"]):
                chosen = dict(candidate)
                chosen["rationale"] = "faster within $0.30"
            else:
                chosen = dict(cheapest)
                chosen["rationale"] = "cheapest"
            return chosen
        # default fallback
        chosen = dict(options[3])
        chosen["rationale"] = "default"
        return chosen

    def handle(self, payload: Dict):
        order = payload.get("order")
        if not order:
            return
        oid = payload["order_id"]
        weight = self.compute_weight(order)
        method = self.choose_method(order)
        changed = {}
        if order.get("computed_weight") != weight:
            changed["computed_weight"] = weight
        if order.get("proposed_shipping_method") != method:
            changed["proposed_shipping_method"] = method
        if changed:
            self.service.update(oid, changed)
            self.ctx.event_bus.publish(
                "order.shipping.selected",
                {"order_id": oid, "method": method},
            )

    # routes -------------------------------------------------------------
    def setup_routes(self, app: Any):
        @app.get("/gl/orders/{oid}/shipping/options")
        def options(oid: str):
            order = self.service.get(oid)
            if not order:
                raise HTTPException(404)
            opts = self.shipping_options(order.dict())[:2]
            return opts

        @app.post("/gl/orders/{oid}/shipping/approve")
        def approve(oid: str):
            order = self.service.get(oid)
            if not order:
                raise HTTPException(404)
            method = order.proposed_shipping_method
            if not method:
                raise HTTPException(400)
            self.service.update(oid, {"approved_shipping_method": method})
            self.ctx.event_bus.publish(
                "order.shipping.approved", {"order_id": oid, "method": method}
            )
            self.service.change_status(oid, "Ship Method Chosen")
            return method
