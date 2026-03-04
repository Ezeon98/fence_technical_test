"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.v1.covenants import router as covenants_router
from app.infrastructure.db.postgres import initialize_database
from app.infrastructure.settings import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(covenants_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        """Return a basic health-check response."""
        return {"status": "ok"}

    @app.on_event("startup")
    def on_startup() -> None:
        """Initialize required infrastructure at startup."""
        initialize_database()

    return app


app = create_app()
