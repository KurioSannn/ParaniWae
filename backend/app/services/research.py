"""Basis pengetahuan publik pencak silat (berkas di content/ & research/) — ADR-0008 public-first.

Sumber kebenaran = berkas yang sama dengan importer (app.content_import). Tidak menyentuh DB dan tidak mengubah status
konten: tidak ada yang ditandai 'terbit' atau 'divalidasi'. Lihat docs/adr/0007-public-research-preview.md.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from app.content_import import (
    ANATOMY_KEYS,
    ANATOMY_LABEL,
    Bundle,
    _cite,
    _dig,
    _resolve,
    load_bundle,
)
from app.core.config import get_settings
from app.core.errors import ApiError

# Tampilan publik tidak menampilkan kutipan/halaman rujukan maupun istilah kemitraan (arahan pemilik produk 2026-11-21).
# Berkas riset di content/ & research/ tetap memuat kutipan lengkap; pembersihan hanya di lapisan keluaran API.
_CITE_PAREN = re.compile(r"\s*\((?:[^()]*?[,\s])?hlm\.[^()]*\)")
_CITE_BARE = re.compile(r"(?:\b[A-Z][a-zA-Z]+(?: dan [A-Z][a-zA-Z]+)? )?hlm\. ?\d+(?:[–-]\d+)?(?:, ?\d+(?:[–-]\d+)?)*;? ?")
_PHRASES = (("instruktur mitra", "pelatih"), ("Instruktur mitra", "Pelatih"), ("perguruan mitra", "perguruan"), ("Perguruan mitra", "Perguruan"),
            ("pelatih mitra", "pelatih"), ("guru mitra", "guru"), ("mitra budaya", "perguruan"))
_SKIP_KEYS = {"notes_markdown"}


def scrub_text(t: str) -> str:
    t = _CITE_PAREN.sub("", t)
    t = _CITE_BARE.sub("", t)
    for a, b in _PHRASES:
        t = t.replace(a, b)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\s+([.,;:)])", r"\1", t)
    t = re.sub(r"\(\s*\)", "", t)
    return t.strip()


def scrub(o):
    """Bersihkan kutipan halaman & istilah mitra dari semua string pada payload publik (rekursif)."""
    if isinstance(o, str):
        return scrub_text(o)
    if isinstance(o, list):
        return [scrub(x) for x in o]
    if isinstance(o, dict):
        return {k: (v if k in _SKIP_KEYS else scrub(v)) for k, v in o.items()}
    return o


SLUG_RE = re.compile(r"^[a-z0-9-]{1,120}$")
DISCLAIMER = (
    "Disusun Redaksi SILATARA dari sumber terbit yang dirujuk per halaman. Materi ini pengantar umum, bukan kurikulum "
    "resmi perguruan tertentu."
)
CATEGORY_LABEL = {
    "sikap_dasar": "Sikap dasar", "kuda_kuda": "Kuda-kuda", "sikap_duduk": "Sikap duduk", "sikap_pasang": "Sikap pasang",
    "arah_langkah": "Arah", "cara_melangkah": "Cara melangkah", "pola_langkah": "Pola langkah",
    "pembelaan_tanpa_kontak": "Pembelaan tanpa kontak",
}  # fmt: skip

_lock = threading.Lock()
_cache: dict = {"key": None, "data": None}


def _root() -> Path:
    s = get_settings()
    if not s.research_preview_enabled:
        raise ApiError(404, "NOT_FOUND", "Tidak ditemukan.")
    root = Path(s.research_repo_dir)
    if not (root / "content" / "pencak-silat").is_dir():
        raise ApiError(503, "RESEARCH_UNAVAILABLE", "Berkas riset tidak tersedia di server.")
    return root


def _stamp(root: Path) -> float:
    files = list((root / "content" / "pencak-silat").rglob("*.json")) + list((root / "research").rglob("*.json"))
    return max((f.stat().st_mtime for f in files), default=0.0)


def data() -> dict:
    root = _root()
    key = (str(root), _stamp(root))
    with _lock:
        if _cache["key"] == key:
            return _cache["data"]
        b = load_bundle(root)
        rd = lambda p: json.loads((root / "research" / "pencak-silat" / p).read_text())  # noqa: E731
        d = {
            "bundle": b,
            "entities": rd("traditions/entities.json"),
            "coverage": rd("national-coverage/provinces.json"),
            "inventory": rd("movement-inventory/inventory.json"),
            "sources_raw": rd("sources/sources.json"),
        }
        _cache.update(key=key, data=d)
        return d


# ------------------------------------------------------------------ ringkasan & katalog
def _count(xs, k):
    out: dict[str, int] = {}
    for x in xs:
        out[x[k]] = out.get(x[k], 0) + 1
    return out


def summary() -> dict:
    d = data()
    b: Bundle = d["bundle"]
    mv = b.movements
    return {
        "disclaimer": DISCLAIMER,
        "as_of": d["coverage"]["as_of"],
        "sources": {"total": len(b.sources), "by_read_status": _count(b.sources.values(), "read_status")},
        "entities": {
            "total": len(d["entities"]["entities"]),
            "by_category": _count(d["entities"]["entities"], "category"),
            "by_verification": _count(d["entities"]["entities"], "verification"),
        },
        "provinces": {
            "total": len(d["coverage"]["provinces"]),
            "by_status": _count(d["coverage"]["provinces"], "status"),
        },
        "movements": {
            "total": len(mv),
            "animated": sum(1 for m in mv if m["animation"]["status"] == "generated"),
            "by_safety": _count(mv, "safety_class"),
            "by_content_status": _count(mv, "content_status"),
        },
        "courses": len(b.courses),
        "lessons": sum(len(v) for v in b.lessons.values()),
        "global_gaps": d["coverage"]["global_gaps"],
        "instructor_validated": 0,
    }


def coverage() -> dict:
    d = data()
    ents = {e["id"]: e for e in d["entities"]["entities"]}
    return {
        "as_of": d["coverage"]["as_of"],
        "legend": d["coverage"]["status_legend"],
        "global_gaps": d["coverage"]["global_gaps"],
        "provinces": [
            {
                **{k: p[k] for k in ("name", "status", "gap")},
                "entities": [
                    {"id": e, "name": ents[e]["name"], "category": ents[e]["category"]}
                    for e in p["entities"]
                    if e in ents
                ],
            }
            for p in d["coverage"]["provinces"]
        ],
    }


def entities(province: str | None = None, category: str | None = None) -> dict:
    d = data()
    b: Bundle = d["bundle"]
    items = []
    for e in d["entities"]["entities"]:
        if category and e["category"] != category:
            continue
        if province and province not in e.get("provinces", []):
            continue
        items.append(
            {
                **{
                    k: e.get(k)
                    for k in (
                        "id",
                        "name",
                        "aliases",
                        "category",
                        "provinces",
                        "localities",
                        "verification",
                        "notes",
                        "founder",
                        "wbtb",
                        "historic_ipsi",
                        "members",
                    )
                },
                "notes": e.get("public_note"),  # catatan kerja internal (notes) tidak dikirim ke publik
                # versi tampilan publik (tanpa anotasi kerja seperti "needs_verification")
                "localities": e.get("public_localities", e.get("localities")),
                "aliases": e.get("public_aliases", e.get("aliases")),
                "provinces": [
                    ("Nasional" if x == "nasional" else "Internasional" if x == "internasional" else x)
                    for x in e.get("provinces", [])
                    if x != "needs_verification"
                ],
                "sources": [{"id": s, "citation": _cite(b, s)} for s in e.get("source_ids", []) if s in b.sources],
            }
        )
    return {"categories": d["entities"]["categories"], "rules": d["entities"]["rules"], "items": items}


def sources() -> list[dict]:
    return [
        {
            k: s.get(k)
            for k in (
                "id",
                "type",
                "title",
                "author_or_publisher",
                "venue",
                "year",
                "url",
                "doi",
                "isbn",
                "read_status",
                "license",
                "supports",
                "note",
            )
        }
        for s in data()["sources_raw"]["sources"]
    ]


def inventory() -> dict:
    inv = data()["inventory"]
    groups = []
    for g in inv["groups"]:
        dfl = g.get("defaults", {})
        groups.append({"label": g["label"], "tradition": g["tradition"], "items": [{**dfl, **it} for it in g["items"]]})
    return {"purpose": inv["purpose"], "groups": groups}


# ------------------------------------------------------------------ gerakan
def _anim_dir(mid: str) -> Path:
    return _root() / "content" / "pencak-silat" / "animations" / mid


def _movement_by_slug(slug: str) -> dict:
    if not SLUG_RE.match(slug):
        raise ApiError(404, "NOT_FOUND", "Gerakan tidak ditemukan.")
    for m in data()["bundle"].movements:
        if m["slug"] == slug:
            return m
    raise ApiError(404, "NOT_FOUND", "Gerakan tidak ditemukan.")


def _anim_summary(m: dict) -> dict:
    an = m["animation"]
    gen = an["status"] == "generated"
    base = f"/api/v1/research/movements/{m['slug']}"
    return {
        "status": an["status"],
        "animation_id": an["animation_id"],
        "url": f"{base}/animation.svg" if gen else None,
        "thumbnail_url": f"{base}/thumbnail.svg" if gen else None,
        "needs": an.get("needs"),
    }


def _trd(b: Bundle, tid: str) -> dict:
    return next(t for t in b.common["traditions"] if t["id"] == tid)


def movement_list(category: str | None = None) -> dict:
    b: Bundle = data()["bundle"]
    items = []
    for m in b.movements:
        if category and m["category"] != category:
            continue
        items.append(
            {
                "slug": m["slug"], "id": m["id"], "name": m["names"]["primary"], "aliases": m["names"]["aliases"],
                "category": m["category"], "category_label": CATEGORY_LABEL.get(m["category"], m["category"]),
                "level": m["level"], "safety_class": m["safety_class"], "solo_form_status": m["solo_form_status"],
                "content_status": m["content_status"], "phases": len(m["phases"]),
                "tradition_slug": _trd(b, m["_tradition_id"])["slug"], "tradition_name": _trd(b, m["_tradition_id"])["name"],
                "summary": _text(m, b, m["cultural_context"]["purpose"])["text"],
                "sources": sorted({r["source_id"] for r in m["references"]}), "animation": _anim_summary(m),
            }
        )  # fmt: skip
    return {"disclaimer": DISCLAIMER, "categories": CATEGORY_LABEL, "items": items}


def _text(m, b, node) -> dict:
    n = _resolve(m, b.shared[m["id"]], b.common, node)
    if not isinstance(n, dict):
        return {"text": str(n), "basis": None, "sources": []}
    return {
        "text": n.get("text", ""),
        "basis": n.get("basis") or ("source" if n.get("source_ids") else None),
        "locator": n.get("locator"),
        "sources": n.get("source_ids", []),
    }


def movement_detail(slug: str) -> dict:
    m = _movement_by_slug(slug)
    b: Bundle = data()["bundle"]
    cm = b.common
    cc = m["cultural_context"]
    pr, pg = m["prerequisites"], m["practice"]
    anat = m.get("anatomy") or {}
    notes_path = _anim_dir(m["id"]) / "ANIMATION_NOTES.md"
    used_in = []
    for c in b.courses:
        for le in b.lessons.get(c["id"], []):
            if m["id"] in le.get("movement_ids", []):
                used_in.append(
                    {
                        "course_slug": c["slug"],
                        "course_title": c["title"],
                        "lesson_slug": le["slug"],
                        "lesson_title": le["title"],
                    }
                )
    return {
        "disclaimer": DISCLAIMER,
        "id": m["id"], "slug": m["slug"], "names": m["names"], "category": m["category"],
        "category_label": CATEGORY_LABEL.get(m["category"], m["category"]), "level": m["level"],
        "safety_class": m["safety_class"], "solo_form_status": m["solo_form_status"], "content_status": m["content_status"],
        "evidence_tier": m["evidence_tier"], "instructor_validation": m["instructor_validation"], "permission_status": m["permission_status"],
        "tradition": _trd(b, m["_tradition_id"])["name"],
        "tradition_slug": _trd(b, m["_tradition_id"])["slug"],
        "cultural": {
            "context": _text(m, b, cc["context"]), "purpose": _text(m, b, cc["purpose"]), "meaning": _text(m, b, cc["meaning"]),
            "terminology": cc.get("terminology", []), "variants": [_text(m, b, v) for v in cc.get("variants", [])],
            "differs_from": cc.get("differs_from", []),
        },
        "prerequisites": {
            "abilities": pr["abilities"], "physical_prep": pr["physical_prep"],
            "space": _dig(cm, pr["space_ref"].split(".")[1:]), "surface": _dig(cm, pr["surface_ref"].split(".")[1:]),
            "equipment": _dig(cm, pr["equipment_ref"].split(".")[1:]), "limits": _dig(cm, pr["limits_ref"].split(".")[1:]),
        },
        "anatomy": [
            {"key": k, "label": ANATOMY_LABEL[k], "text": anat[k]["text"] if k in anat else cm["anatomy_missing_text"],
             "basis": anat[k]["basis"] if k in anat else "needs_validation", "sources": anat.get(k, {}).get("source_ids", [])}
            for k in ANATOMY_KEYS
        ],
        "phases": m["phases"],
        "practice": {**{k: pg[k] for k in ("start", "sequence", "tempo", "repetitions", "easier", "progression", "cooldown")},
                     "stop_when": _dig(cm, pg["stop_when_ref"].split(".")[1:]) or [], "stop_basis": cm["safety"]["stop_basis"]},
        "common_mistakes": m.get("common_mistakes", []), "common_mistakes_gap": m.get("common_mistakes_gap"),
        "references": [{**r, "citation": _cite(b, r["source_id"]), "url": b.sources[r["source_id"]].get("url")} for r in m["references"]],
        "gaps": m.get("gaps", []),
        "animation": {**_anim_summary(m), "notes_markdown": notes_path.read_text() if notes_path.exists() else None},
        "used_in": used_in,
    }  # fmt: skip


def animation_file(slug: str, name: str) -> bytes:
    if name not in ("animation.svg", "thumbnail.svg"):
        raise ApiError(404, "NOT_FOUND", "Tidak ditemukan.")
    m = _movement_by_slug(slug)
    if m["animation"]["status"] != "generated":
        raise ApiError(404, "NOT_FOUND", "Animasi belum tersedia (needs_reference).")
    p = _anim_dir(m["id"]) / name
    if not p.is_file():
        raise ApiError(404, "NOT_FOUND", "Berkas animasi belum dibangun.")
    return p.read_bytes()


# ------------------------------------------------------------------ kurikulum
def curricula() -> dict:
    b: Bundle = data()["bundle"]
    trd = {t["id"]: t["name"] for t in b.common["traditions"]}
    out = []
    for c in b.courses:
        ls = b.lessons.get(c["id"], [])
        out.append(
            {
                **{
                    k: c.get(k)  # editorial_note opsional
                    for k in (
                        "id",
                        "slug",
                        "title",
                        "summary",
                        "level",
                        "estimated_minutes",
                        "safety_notes",
                        "content_status",
                        "instructor_validation",
                        "editorial_note",
                    )
                },
                "tradition": trd.get(c["tradition_id"], c["tradition_id"]),
                "modules": [
                    {
                        **mod,
                        "lessons": [
                            {k: le[k] for k in ("slug", "title", "description", "duration_min", "order")}
                            for le in ls
                            if le["module_id"] == mod["id"]
                        ],
                    }
                    for mod in c["modules"]
                ],
            }
        )
    return {"disclaimer": DISCLAIMER, "items": out}


def lesson(course_slug: str, lesson_slug: str) -> dict:
    if not (SLUG_RE.match(course_slug) and SLUG_RE.match(lesson_slug)):
        raise ApiError(404, "NOT_FOUND", "Pelajaran tidak ditemukan.")
    b: Bundle = data()["bundle"]
    c = next((x for x in b.courses if x["slug"] == course_slug), None)
    le = next((x for x in b.lessons.get(c["id"], []) if x["slug"] == lesson_slug), None) if c else None
    if not le:
        raise ApiError(404, "NOT_FOUND", "Pelajaran tidak ditemukan.")
    ls = b.lessons[c["id"]]
    i = ls.index(le)
    mv = {m["id"]: m for m in b.movements}
    return {
        "disclaimer": DISCLAIMER,
        "course": {"slug": c["slug"], "title": c["title"]},
        "module": next(m["title"] for m in c["modules"] if m["id"] == le["module_id"]),
        **{k: le.get(k) for k in ("slug", "title", "description", "objectives", "prior_competence", "duration_min", "equipment", "space", "safety_briefing", "theory", "cultural_explanation", "practice_steps", "summary", "reflection", "quiz")},
        "references": [{**r, "citation": _cite(b, r["source_id"]), "url": b.sources[r["source_id"]].get("url")} for r in le.get("references", [])],
        "movements": [
            {"slug": mv[x]["slug"], "name": mv[x]["names"]["primary"], "safety_class": mv[x]["safety_class"], "phases": mv[x]["phases"],
             "common_mistakes": mv[x].get("common_mistakes", []), "common_mistakes_gap": mv[x].get("common_mistakes_gap"), "animation": _anim_summary(mv[x])}
            for x in le.get("movement_ids", [])
        ],
        "prev": {"slug": ls[i - 1]["slug"], "title": ls[i - 1]["title"]} if i > 0 else None,
        "next": {"slug": ls[i + 1]["slug"], "title": ls[i + 1]["title"]} if i + 1 < len(ls) else None,
        "instructor_validation": "not_validated",
    }  # fmt: skip


# ------------------------------------------------------------------ tradisi & kursus (untuk halaman Warisan/Akademi)
def _entity_brief(d: dict, ids: list[str]) -> list[dict]:
    ents = {e["id"]: e for e in d["entities"]["entities"]}
    return [
        {
            **{k: ents[i].get(k) for k in ("id", "name", "category")},
            "provinces": [x for x in ents[i].get("provinces", []) if x not in ("needs_verification", "nasional")],
            "localities": ents[i].get("public_localities", ents[i].get("localities")),
            "notes": ents[i].get("public_note"),
        }
        for i in ids
        if i in ents
    ]


def _course_brief(c: dict, ls: list[dict]) -> dict:
    return {
        **{k: c.get(k) for k in ("slug", "title", "summary", "level", "estimated_minutes")},
        "lesson_count": len(ls),
        "module_count": len(c["modules"]),
    }


def traditions() -> list[dict]:
    d = data()
    b: Bundle = d["bundle"]
    out = []
    for t in b.common["traditions"]:
        mvs = [m for m in b.movements if m["_tradition_id"] == t["id"]]
        crs = [c for c in b.courses if c["tradition_id"] == t["id"]]
        out.append(
            {
                **{k: t.get(k) for k in ("slug", "name", "local_name", "region", "public_summary", "provinces")},
                "movement_count": len(mvs),
                "animated_count": sum(1 for m in mvs if m["animation"]["status"] == "generated"),
                "course_count": len(crs),
                "related_entity_count": len(t.get("related_entities", [])),
            }
        )
    return out


def tradition_detail(slug: str) -> dict:
    if not SLUG_RE.match(slug):
        raise ApiError(404, "NOT_FOUND", "Tradisi tidak ditemukan.")
    d = data()
    b: Bundle = d["bundle"]
    t = next((x for x in b.common["traditions"] if x["slug"] == slug), None)
    if t is None:
        raise ApiError(404, "NOT_FOUND", "Tradisi tidak ditemukan.")
    mvs = [x for x in movement_list()["items"] if x["tradition_slug"] == slug]
    crs = [_course_brief(c, b.lessons.get(c["id"], [])) for c in b.courses if c["tradition_id"] == t["id"]]
    return {
        **{k: t.get(k) for k in ("slug", "name", "local_name", "region", "public_summary", "provinces")},
        "movements": mvs,
        "courses": crs,
        "related_entities": _entity_brief(d, t.get("related_entities", [])),
        "references": [
            {"source_id": s, "citation": _cite(b, s), "url": b.sources[s].get("url")} for s in t["source_ids"]
        ],
    }


def course_detail(slug: str) -> dict:
    if not SLUG_RE.match(slug):
        raise ApiError(404, "NOT_FOUND", "Kursus tidak ditemukan.")
    b: Bundle = data()["bundle"]
    c = next((x for x in b.courses if x["slug"] == slug), None)
    if c is None:
        raise ApiError(404, "NOT_FOUND", "Kursus tidak ditemukan.")
    ls = b.lessons.get(c["id"], [])
    mv = {m["id"]: m for m in b.movements}
    taught = list(dict.fromkeys(x for le in ls for x in le.get("movement_ids", [])))
    refs = list(
        dict.fromkeys([s for s in c["source_ids"]] + [r["source_id"] for le in ls for r in le.get("references", [])])
    )
    t = _trd(b, c["tradition_id"])
    return {
        **_course_brief(c, ls),
        "safety_notes": c.get("safety_notes"),
        "goals": c.get("goals", []),
        "tradition": {"slug": t["slug"], "name": t["name"]},
        "modules": [
            {**{k: mod[k] for k in ("order", "title", "summary")},
             "lessons": [{k: le[k] for k in ("slug", "title", "description", "duration_min", "order")} for le in ls if le["module_id"] == mod["id"]]}
            for mod in c["modules"]
        ],
        "movements": [
            {"slug": mv[x]["slug"], "name": mv[x]["names"]["primary"], "safety_class": mv[x]["safety_class"], "animation": _anim_summary(mv[x])}
            for x in taught
        ],
        "references": [{"source_id": s, "citation": _cite(b, s), "url": b.sources[s].get("url")} for s in refs if s in b.sources],
    }  # fmt: skip
