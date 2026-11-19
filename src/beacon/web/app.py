from __future__ import annotations

import secrets
import webbrowser
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from beacon import __version__

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def create_app(session_token: str | None = None) -> FastAPI:
    """Create and configure the local Beacon FastAPI application."""
    app = FastAPI(
        title="Beacon Local Web UI",
        version=__version__,
        docs_url=None,
        redoc_url=None,
    )
    app.state.session_token = session_token or secrets.token_urlsafe(32)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "version": __version__,
                "session_token": app.state.session_token,
            },
        )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {
            "status": "wip",
            "version": __version__,
            "message": "Web dashboard UI skeleton ready; live WebSocket stream pending.",
        }

    return app


def run_web_dashboard(
    interval: float = 1.0,
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Start the local Uvicorn server bound strictly to 127.0.0.1."""
    import uvicorn

    token = secrets.token_urlsafe(32)
    app = create_app(session_token=token)
    url = f"http://127.0.0.1:{port}"

    if open_browser:
        webbrowser.open(url)

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")