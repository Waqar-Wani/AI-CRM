from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin_properties, user_properties, chat
from app.db.init_db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="AI CRM Demo (Real Estate)")

    # Demo-friendly CORS (lock down for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    app.include_router(admin_properties.router, prefix="/admin", tags=["admin"])
    app.include_router(user_properties.router, tags=["properties"])
    app.include_router(chat.router, tags=["chat"])

    return app


app = create_app()
