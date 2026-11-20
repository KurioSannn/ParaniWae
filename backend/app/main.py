from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    academy,
    admin,
    auth,
    catalog,
    dev,
    health,
    manage,
    media,
    practice,
    studio_movements,
    studio_partners,
)
from app.core.config import get_settings
from app.core.errors import RequestIdMiddleware, install_error_handlers

DESCRIPTION = """
API SILATARA (tahap pengembangan). Autentikasi: cookie sesi HttpOnly + header `X-CSRF-Token`
untuk request mutasi (lihat docs/adr/0002-authentication.md). Semua konten publik hanya
berstatus `published`; data **[DEMO]** adalah contoh teknis, bukan materi budaya resmi.
Format error: `{"error": {"code", "message", "details", "request_id"}}`.
"""


def create_app() -> FastAPI:
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
    app.add_middleware(RequestIdMiddleware)
    for r in (health.router, auth.router, catalog.router, academy.router, manage.router,
              admin.router, dev.router, practice.router, studio_partners.router, studio_movements.router,
              media.router):
        app.include_router(r, prefix="/api/v1")
    return app


app = create_app()
