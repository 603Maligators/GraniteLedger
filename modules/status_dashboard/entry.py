import os
from typing import Any

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI  # type: ignore

    class HTMLResponse(str):
        pass

    class StaticFiles:  # minimal stub
        def __init__(self, directory: str):
            self.directory = directory


class DashboardModule:
    def on_load(self, ctx):
        self.ctx = ctx
        ctx.registry.bind("ui.dashboard@1.0", self)

    def setup_routes(self, app: Any):
        static_dir = os.path.join(self.ctx.module_path, "static")
        if hasattr(app, "mount"):
            app.mount("/gl/ui/static", StaticFiles(directory=static_dir), name="gl_ui_static")

            @app.get("/gl/ui", response_class=HTMLResponse)
            def ui():
                path = os.path.join(static_dir, "index.html")
                with open(path, "r", encoding="utf-8") as fh:
                    return fh.read()
        else:
            @app.get("/gl/ui")
            def ui():
                path = os.path.join(static_dir, "index.html")
                with open(path, "r", encoding="utf-8") as fh:
                    return fh.read()
