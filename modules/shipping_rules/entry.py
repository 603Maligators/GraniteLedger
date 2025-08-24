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
        # deterministic stub options
        return [
            {"carrier": "USPS", "service": "Ground", "cost": 5.0, "eta_days": 5},
            {"carrier": "UPS", "service": "Ground", "cost": 5.2, "eta_days": 3},
            {"carrier": "USPS", "service": "Priority", "cost": 8.0, "eta_days": 2},
            {"carrier": "Home", "service": "Delivery", "cost": 7.0, "eta_days": 4},
        ]

    def choose_method(self, order: Dict) -> Dict:
        zip_code = order["destination"]["zip"]
        tier = order.get("shipping_tier")
        options = self.shipping_options(order)
        # ZIP override
        if zip_code == "03224":
            return {"carrier": "Home", "service": "Delivery", "cost": 7.0, "eta_days": 4, "rationale": "zip override"}
        if tier == "Priority":
            if zip_code == "03224":
                return {
                    "carrier": "Home",
                    "service": "Delivery",
                    "cost": 7.0,
                    "eta_days": 4,
                    "rationale": "priority zip override",
                }
            return {
                "carrier": "USPS",
                "service": "Priority",
                "cost": 8.0,
                "eta_days": 2,
                "rationale": "priority",
            }
        if tier == "Free":
            opts = sorted(options[:2], key=lambda o: o["cost"])
            cheapest = opts[0]
            candidate = opts[1]
            if candidate["cost"] - cheapest["cost"] < 0.3 and candidate["eta_days"] < cheapest["eta_days"]:
                chosen = candidate
                rationale = "faster within $0.30"
            else:
                chosen = cheapest
                rationale = "cheapest"
            chosen = dict(chosen)
            chosen["rationale"] = rationale
            return chosen
        # default
        return {"carrier": "Home", "service": "Delivery", "cost": 7.0, "eta_days": 4, "rationale": "default"}

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
                    "method": method,
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
            data = order.dict()
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
            rationale = (
                method.get("rationale") if isinstance(method, dict) else method.rationale
            )
            self.service.update(oid, {"approved_shipping_method": method})
            self.ctx.event_bus.publish(
                "order.shipping.approved",
                {"order_id": oid, "method": method, "rationale": rationale},
            )
            try:
                self.service.change_status(oid, "Ship Method Chosen")
            except ValueError:
                raise HTTPException(409)
            return method
