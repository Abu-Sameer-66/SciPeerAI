# src/scipeerai/api/__init__.py

from fastapi import FastAPI
from src.scipeerai.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="SciPeerAI",
        description=(
            "Automated Scientific Integrity & Peer Review Analysis. "
            "Upload paper text and get back a structured integrity report."
        ),
        version="0.1.0",
    )

    # register all routes from routes.py
    app.include_router(router)

    @app.get("/", tags=["System"])
    def health_check():
        return {
            "status": "online",
            "system": "SciPeerAI",
            "version": "0.1.0",
            "message": "Scientific Integrity Engine is running"
        }

    return app