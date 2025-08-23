import os
from typing import Any

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, Response
except ModuleNotFoundError:  # pragma: no cover
    from mini_fastapi import FastAPI, Response  # type: ignore
    HTMLResponse = Response  # type: ignore


class DashboardModule:
    def on_load(self, ctx):
        self.ctx = ctx
        ctx.registry.bind("ui.dashboard@1.0", self)

    def setup_routes(self, app: Any):
        static_dir = os.path.join(self.ctx.module_path, "static")

        @app.get("/gl/ui", response_class=HTMLResponse)
        def ui():
            path = os.path.join(static_dir, "index.html")
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read()

        @app.get("/gl/ui/static/{fname}")
        def assets(fname: str):
            path = os.path.join(static_dir, fname)
            if not os.path.exists(path):
                from forgecore.admin_api import HTTPException

                raise HTTPException(404)
            with open(path, "rb") as fh:
                data = fh.read()
            mime = "text/plain"
            if fname.endswith(".js"):
                mime = "application/javascript"
            elif fname.endswith(".css"):
                mime = "text/css"
            elif fname.endswith(".html"):
                mime = "text/html"
            return Response(content=data, media_type=mime)
