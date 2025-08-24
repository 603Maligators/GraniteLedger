from forgecore.runtime import create_runtime
from forgecore.admin_api import create_app
import os


def build_app():
    base = os.path.dirname(os.path.abspath(__file__))
    modules_path = os.path.join(base, "modules")
    rt = create_runtime(modules_path)
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
