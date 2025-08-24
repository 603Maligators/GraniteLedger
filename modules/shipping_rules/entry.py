from typing import Any, Dict, List
from datetime import datetime
from forgecore.admin_api import HTTPException
import hashlib
import random

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
        zip_code = order["destination"]["zip"]
        weight = order.get("computed_weight") or self.compute_weight(order)
        seed = int(hashlib.sha1(f"{zip_code}-{round(weight,1)}".encode()).hexdigest(), 16)
        rng = random.Random(seed)
        opts = []
        # base options: USPS Ground, UPS Ground, USPS Priority
        cost1 = round(5.0 + rng.uniform(0, 0.05), 2)
        cost2 = round(5.1 + rng.uniform(0, 0.05), 2)
        cost3 = round(7.8 + rng.uniform(0, 0.05), 2)
        opts.append({"carrier": "USPS", "service": "Ground", "cost": cost1, "eta_days": 5})
        opts.append({"carrier": "UPS", "service": "Ground", "cost": cost2, "eta_days": 4})
        opts.append({"carrier": "USPS", "service": "Priority", "cost": cost3, "eta_days": 2})
        opts.append({"carrier": "Home", "service": "Delivery", "cost": 7.0, "eta_days": 3})
        return opts

    def choose_method(self, order: Dict) -> Dict:
        zip_code = order["destination"]["zip"]
        tier = order.get("shipping_tier")
        options = self.shipping_options(order)
        # ZIP override always forces Home Delivery
        if zip_code == "03224":
            return {
                "carrier": "Home",
                "service": "Delivery",
                "cost": 7.0,
                "eta_days": 3,
                "rationale": "ZIP 03224 requires Home Delivery",
            }
        if tier == "Priority":
            return {
                "carrier": "USPS",
                "service": "Priority",
                "cost": next(o["cost"] for o in options if o["service"] == "Priority"),
                "eta_days": 2,
                "rationale": "Customer paid for Priority",
            }
        if tier == "Free":
            ground = options[:2]
            ground.sort(key=lambda o: o["cost"])
            cheapest, candidate = ground
            diff = round(candidate["cost"] - cheapest["cost"], 2)
            eta_diff = cheapest["eta_days"] - candidate["eta_days"]
            if diff < 0.3 and eta_diff > 0:
                chosen = dict(candidate)
                chosen["rationale"] = f"${diff:.2f} more and {eta_diff} day sooner"
            else:
                chosen = dict(cheapest)
                chosen["rationale"] = "Cheapest overall"
            return chosen
        # default
        return {
            "carrier": "Home",
            "service": "Delivery",
            "cost": 7.0,
            "eta_days": 3,
            "rationale": "Default rule",
        }

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
                {
                    "order_id": oid,
                    "detail": f"{method['carrier']} {method['service']}",
                    "rationale": method.get("rationale"),
                },
            )

    # routes -------------------------------------------------------------
    def setup_routes(self, app: Any):
        @app.get("/gl/orders/{oid}/shipping/options")
        def options(oid: str):
            order = self.service.get(oid)
            if not order:
                raise HTTPException(404)
            data = order.model_dump()
            opts = self.shipping_options(data)[:2]
            chosen = self.choose_method(data)
            for o in opts:
                if o["carrier"] == chosen.get("carrier") and o["service"] == chosen.get("service"):
                    o["rationale"] = chosen.get("rationale")
                else:
                    o["rationale"] = ""
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
