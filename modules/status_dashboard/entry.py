import os
from typing import Any

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI as HTMLResponse  # type: ignore


class DashboardModule:
    def on_load(self, ctx):
        self.ctx = ctx
        ctx.registry.bind("ui.dashboard@1.0", self)

    def setup_routes(self, app: Any):
        @app.get("/gl/ui")
        def ui():
            path = os.path.join(self.ctx.module_path, "static", "index.html")
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read()

        @app.get("/gl/ui/{path}")
        def assets(path: str):
            file_path = os.path.join(self.ctx.module_path, "static", path)
            with open(file_path, "r", encoding="utf-8") as fh:
                return fh.read()
