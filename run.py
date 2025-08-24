import os
import sys

BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE, "ForgeCore"))

from forgecore.runtime import create_runtime
from forgecore.admin_api import create_app


def build_app():
    rt = create_runtime("modules")
    rt.start()
    app = create_app(rt)
    for state in rt.loader.modules.values():
        if hasattr(state.instance, "setup_routes"):
            state.instance.setup_routes(app)
    return app, rt


if __name__ == "__main__":
    app, _ = build_app()
    # when running via 'python run.py', start uvicorn if available
    try:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8765)
    except Exception:
        from forgecore.admin_api import Response

        print("App built. Use a WSGI server to run.")
