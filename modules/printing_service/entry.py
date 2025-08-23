import os
from datetime import datetime
from typing import Any
from forgecore.admin_api import HTTPException

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI


class PrintingServiceModule:
    def on_load(self, ctx):
        self.ctx = ctx
        self.service = None
        ctx.registry.bind("printing.service@1.0", self)

    def on_enable(self):
        self.service = self.ctx.registry.get("orders.service@1.0")

    # helpers ------------------------------------------------------------
    def _write_file(self, kind: str, oid: str, content: str) -> str:
        base = self.ctx.storage._module_dir(self.ctx.manifest["name"])  # type: ignore
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        path = os.path.join(base, kind, oid)
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, f"{ts}.txt")
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return file_path

    # core operations ---------------------------------------------------
    def op_print_invoice(self, oid: str, test: bool = False):
        order = self.service.get(oid)
        if not order:
            raise HTTPException(404)
        path = self._write_file("invoices", oid, f"Invoice for {oid}")
        self.ctx.event_bus.publish("order.invoice.printed", {"order_id": oid, "detail": path, "test": test})
        self.service.change_status(oid, "Printed")
        return {"path": path}

    def op_print_label(self, oid: str, test: bool = False):
        order = self.service.get(oid)
        if not order:
            raise HTTPException(404)
        if not order.approved_shipping_method:
            raise HTTPException(400)
        tracking = f"TRK{int(datetime.utcnow().timestamp())}"
        path = self._write_file("labels", oid, f"Label {tracking}")
        self.service.update(oid, {"tracking_number": tracking})
        self.ctx.event_bus.publish("order.label.purchased", {"order_id": oid, "detail": tracking, "test": test})
        self.ctx.event_bus.publish("order.label.printed", {"order_id": oid, "detail": path, "test": test})
        self.service.change_status(oid, "Shipped")
        return {"path": path, "tracking": tracking}

    def op_reprint_invoice(self, oid: str, test: bool = False):
        path = self._write_file("invoices", oid, f"Invoice for {oid} reprint")
        self.ctx.event_bus.publish("order.invoice.printed", {"order_id": oid, "detail": path, "test": test})
        return {"path": path}

    def op_reprint_label(self, oid: str, test: bool = False):
        order = self.service.get(oid)
        if not order or not order.tracking_number:
            raise HTTPException(404)
        path = self._write_file("labels", oid, f"Label {order.tracking_number} reprint")
        self.ctx.event_bus.publish("order.label.printed", {"order_id": oid, "detail": path, "test": test})
        return {"path": path}

    def op_void_rebuy(self, oid: str, test: bool = False):
        order = self.service.get(oid)
        if not order or not order.tracking_number:
            raise HTTPException(404)
        self.ctx.event_bus.publish("order.label.voided", {"order_id": oid, "detail": order.tracking_number, "test": test})
        tracking = f"TRK{int(datetime.utcnow().timestamp())}R"
        path = self._write_file("labels", oid, f"Label {tracking}")
        self.service.update(oid, {"tracking_number": tracking})
        self.ctx.event_bus.publish("order.label.purchased", {"order_id": oid, "detail": tracking, "test": test})
        self.ctx.event_bus.publish("order.label.printed", {"order_id": oid, "detail": path, "test": test})
        return {"path": path, "tracking": tracking}

    # API ---------------------------------------------------------------
    def setup_routes(self, app: Any):
        @app.post("/gl/orders/{oid}/print/invoice")
        def r_print_invoice(oid: str):
            return self.op_print_invoice(oid)

        @app.post("/gl/orders/{oid}/print/label")
        def r_print_label(oid: str):
            return self.op_print_label(oid)

        @app.post("/gl/orders/{oid}/reprint/invoice")
        def r_reprint_invoice(oid: str):
            return self.op_reprint_invoice(oid)

        @app.post("/gl/orders/{oid}/reprint/label")
        def r_reprint_label(oid: str):
            return self.op_reprint_label(oid)

        @app.post("/gl/orders/{oid}/label/void-rebuy")
        def r_void_rebuy(oid: str):
            return self.op_void_rebuy(oid)
