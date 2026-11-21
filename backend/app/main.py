from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    academy,
    admin,
    assessments,
    auth,
    catalog,
    dev,
    directory,
    health,
    manage,
    media,
    pilot,
    practice,
    research,
    studio_movements,
    studio_partners,
)
from app.core.cache_headers import CacheHeadersMiddleware
from app.core.config import get_settings
from app.core.errors import RequestIdMiddleware, install_error_handlers
from app.core.logging import setup_logging

DESCRIPTION = """
API SILATARA (tahap pengembangan). Autentikasi: cookie sesi HttpOnly + header `X-CSRF-Token`
untuk request mutasi (lihat docs/adr/0002-authentication.md). Semua konten publik hanya
berstatus `published`; data **[DEMO]** adalah contoh teknis, bukan materi budaya resmi.
Format error: `{"error": {"code", "message", "details", "request_id"}}`.
"""


def create_app() -> FastAPI:
    setup_logging()
    s = get_settings()
    s.validate_runtime()  # gagal cepat bila konfigurasi produksi tidak aman
    app = FastAPI(title=s.app_name, version=s.app_version, description=DESCRIPTION)
    install_error_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origin_list,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID", "X-CSRF-Token"],
        allow_credentials=True,
    )
    if s.debug_query_stats:
        from app.core.query_stats import QueryStatsMiddleware
        app.add_middleware(QueryStatsMiddleware)
    app.add_middleware(CacheHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    for r in (health.router, auth.router, catalog.router, academy.router, manage.router,
              admin.router, dev.router, practice.router, studio_partners.router, studio_movements.router,
              media.router, pilot.router, research.router, directory.router, assessments.router):
        app.include_router(r, prefix="/api/v1")

    @app.get("/", include_in_schema=False)
    def root():
        frontend_url = s.cors_origins.split(",")[0].strip() if s.cors_origins else "http://localhost:3010"
        return {
            "service": s.app_name,
            "version": s.app_version,
            "message": "SILATARA Backend REST API aktif.",
            "docs": "/docs",
            "health": "/api/v1/health",
            "frontend_ui": frontend_url,
        }

    return app


app = create_app()
