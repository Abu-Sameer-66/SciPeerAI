# FastAPI application factory
from fastapi import FastAPI


def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    Factory pattern — clean, testable, scalable.
    """
    app = FastAPI(
        title="SciPeerAI",
        description="Automated Scientific Integrity & Peer Review Analysis",
        version="0.1.0",
    )

    @app.get("/")
    def health_check():
        return {
            "status": "online",
            "system": "SciPeerAI",
            "version": "0.1.0",
            "message": "Scientific Integrity Engine is running"
        }

    @app.get("/api/v1/status")
    def system_status():
        return {
            "modules": [
                "stat_audit",
                "figure_forensics",
                "methodology_checker",
                "citation_analyzer",
                "reproducibility",
                "novelty_scorer"
            ],
            "ready": False,
            "version": "0.1.0"
        }

    return app