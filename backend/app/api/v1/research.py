"""API publik basis pengetahuan pencak silat (hanya-baca; sumber: content/ & research/). Dipakai halaman utama
Warisan, Pustaka Gerakan, Akademi, dan Perguruan (ADR-0008). Mati bila RESEARCH_PREVIEW_ENABLED=false."""

from fastapi import APIRouter, Request, Response
from fastapi.responses import FileResponse

from app.services import assets3d
from app.services import research as svc

router = APIRouter(prefix="/research", tags=["research"])

SVG_HEADERS = {
    # SVG statis tanpa skrip; CSP ketat bila dibuka langsung di tab.
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "public, max-age=300",
}


@router.get("/summary", summary="Ringkasan hasil riset (jumlah sumber, entitas, provinsi, gerakan, kurikulum)")
def summary():
    return svc.scrub(svc.summary())


@router.get("/coverage", summary="Cakupan 38 provinsi")
def coverage():
    return svc.scrub(svc.coverage())


@router.get("/entities", summary="Katalog tradisi/aliran/perguruan/organisasi")
def entities(province: str | None = None, category: str | None = None):
    return svc.scrub(svc.entities(province, category))


@router.get("/sources", summary="Ledger sumber")
def sources():
    return svc.sources()


@router.get("/inventory", summary="Inventaris nama gerak (termasuk yang belum terdokumentasi)")
def inventory():
    return svc.scrub(svc.inventory())


@router.get("/movements", summary="Daftar gerakan terdokumentasi")
def movements(category: str | None = None):
    return svc.scrub(svc.movement_list(category))


@router.get("/movements/{slug}", summary="Dokumen gerakan lengkap")
def movement(slug: str):
    return svc.scrub(svc.movement_detail(slug))


@router.get("/movements/{slug}/{name}", summary="Animasi SVG (animation.svg / thumbnail.svg)")
def animation(slug: str, name: str):
    return Response(svc.animation_file(slug, name), media_type="image/svg+xml", headers=SVG_HEADERS)


@router.get("/traditions", summary="Tradisi dalam basis pengetahuan")
def traditions():
    return svc.scrub(svc.traditions())


@router.get("/traditions/{slug}", summary="Detail tradisi: gerakan, kursus, entitas terkait, rujukan")
def tradition(slug: str):
    return svc.scrub(svc.tradition_detail(slug))


@router.get("/courses/{slug}", summary="Detail kursus pengetahuan publik")
def course(slug: str):
    return svc.scrub(svc.course_detail(slug))


@router.get("/curricula", summary="Kurikulum & struktur kelas")
def curricula():
    return svc.scrub(svc.curricula())


@router.get("/curricula/{course_slug}/{lesson_slug}", summary="Isi pelajaran lengkap")
def lesson(course_slug: str, lesson_slug: str):
    return svc.scrub(svc.lesson(course_slug, lesson_slug))


@router.get("/character", summary="Karakter instruksional 3D: metadata, mesh, dan daftar klip beserta penanda fase")
def character():
    return assets3d.character()


@router.get("/character/model.glb", summary="Model GLB (glTF 2.0 biner) karakter + semua klip")
def character_glb(request: Request):
    path, sha = assets3d.glb()
    etag = f'"{sha[:32]}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return FileResponse(path, media_type="model/gltf-binary", headers={
        "ETag": etag, "Cache-Control": "public, max-age=3600", "X-Content-Type-Options": "nosniff"})


@router.get("/character/reference/{movement_id}", summary="Urutan titik tubuh referensi (indeks MediaPipe), klip 3D")
def character_reference(movement_id: str):
    return assets3d.reference(movement_id)


@router.get("/assessment/protocols", summary="Daftar protokol penilaian gerak + kesiapan setiap gerakan")
def assessment_protocols():
    return assets3d.protocols()


@router.get("/assessment/protocols/{movement_id}", summary="Protokol penilaian satu gerakan")
def assessment_protocol(movement_id: str):
    return assets3d.protocol(movement_id)
