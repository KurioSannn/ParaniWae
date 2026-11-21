"""Importer konten riset pencak silat → DRAF di database (idempoten, DRY-RUN default, tidak pernah menerbitkan).

Sumber berkas (lihat docs/PENCAK_SILAT_CONTENT_CONTRACT.md):
  <repo>/content/pencak-silat/{catalog,movements,curricula,lessons,animations}
  <repo>/research/pencak-silat/sources/sources.json

Aturan yang ditegakkan kode (bukan sekadar konvensi):
- Semua baris yang ditulis berstatus `draft`; gerakan selalu `practice_mode='not_for_practice'`, `assessment_enabled=false`.
- Baris yang sudah masuk alur review (status selain draft/needs_revision/rejected) TIDAK diubah. Untuk dokumen gerakan
  yang versi terakhirnya published/archived dibuat versi draf baru (+changelog); bila ada versi yang sedang ditinjau,
  gerakan dilewati (`blocked_review`).
- Pemilik teknis draf = partner internal "Tim Editorial SILATARA" (bukan mitra budaya; ADR-0006).
- Konten tidak boleh mengklaim validasi instruktur: `instructor_validation` wajib `not_validated`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Course,
    CourseModule,
    CulturalTradition,
    Lesson,
    LessonMaterial,
    Movement,
    MovementDocument,
    MovementPhase,
    Partner,
    TraditionPartner,
    User,
)
from app.services import audit

ID_RE = {
    "source": re.compile(r"^src\.[a-z0-9-]+(\.[a-z0-9-]+)*$"),
    "tradition": re.compile(r"^trd\.[a-z0-9-]+$"),
    "movement": re.compile(r"^mv\.[a-z0-9-]+\.[a-z0-9-]+$"),
    "phase": re.compile(r"^mv\.[a-z0-9-]+\.[a-z0-9-]+#p\d+$"),
    "animation": re.compile(r"^anim\.[a-z0-9-]+\.[a-z0-9-]+\.v\d+$"),
    "course": re.compile(r"^crs\.[a-z0-9-]+$"),
    "module": re.compile(r"^crs\.[a-z0-9-]+\.m\d{2}$"),
    "lesson": re.compile(r"^crs\.[a-z0-9-]+\.l\d{2}$"),
}
CONTENT_STATUSES = {"draft", "needs_reference"}
SAFETY = {"solo_beginner", "solo_intermediate", "solo_advanced", "supervised_only", "partner_required", "restricted"}
SAFETY_DB = {
    "solo_beginner": "solo_beginner",
    "solo_intermediate": "supervised_practice",
    "solo_advanced": "supervised_practice",
    "supervised_only": "supervised_practice",
    "partner_required": "contact_practice",
    "restricted": "restricted",
}
SOLO_STATUS = {"documented_solo", "inferred_not_documented", "partner_form"}
BASIS = {"source", "editorial", "needs_validation", "gap", "source+editorial", "editorial_unvalidated"}
ANATOMY_KEYS = (
    "head", "shoulders", "torso", "hips", "arms", "elbows", "wrists", "legs", "knees", "ankles", "feet", "weight", "orientation",
)  # fmt: skip
ANATOMY_LABEL = {
    "head": "Kepala/pandangan", "shoulders": "Bahu", "torso": "Badan", "hips": "Pinggul", "arms": "Lengan/tangan",
    "elbows": "Siku", "wrists": "Pergelangan tangan", "legs": "Tungkai", "knees": "Lutut", "ankles": "Pergelangan kaki",
    "feet": "Telapak kaki", "weight": "Distribusi berat", "orientation": "Orientasi",
}  # fmt: skip
# Indeks MediaPipe Pose (33 titik)
LANDMARKS = {
    "nose": 0, "left_shoulder": 11, "right_shoulder": 12, "left_elbow": 13, "right_elbow": 14, "left_wrist": 15,
    "right_wrist": 16, "left_hip": 23, "right_hip": 24, "left_knee": 25, "right_knee": 26, "left_ankle": 27,
    "right_ankle": 28, "left_heel": 29, "right_heel": 30, "left_foot_index": 31, "right_foot_index": 32,
}  # fmt: skip
EDITABLE = {"draft", "needs_revision", "rejected"}


def _can_update(row) -> bool:
    """Baris boleh diperbarui importer: masih draf/revisi, ATAU pengetahuan berbasis sumber milik pipeline impor."""
    return row.status in EDITABLE or (
        getattr(row, "content_basis", None) == CONTENT_BASIS and (row.review_note or "").startswith(IMPORT_TAG)
    )


IMMUTABLE_DOC = {"pending_review", "verified", "published", "archived"}
USAGE_SCOPE = (
    "Pengetahuan umum disusun Redaksi SILATARA dari sumber terbit (parafrasa dengan rujukan halaman). Bukan kurikulum "
    "resmi perguruan mana pun; tidak memuat media berlisensi. Untuk klaim resmi suatu perguruan diperlukan konfirmasi mitra."
)
CONTENT_BASIS = "source_backed"  # semua konten riset = pengetahuan berbasis sumber (ADR-0008)
EDITORIAL_EVIDENCE = (
    "Tinjauan editorial sumber (ADR-0008): setiap klaim dirujuk ke sumber terbit yang dibaca utuh; "
    "bukan konfirmasi mitra/instruktur."
)
SAFETY_TEXT = {
    "solo_beginner": "Dapat dipelajari mandiri secara perlahan di ruang yang lapang dan lantai yang tidak licin.",
    "solo_intermediate": "Melatih keseimbangan; berlatihlah di dekat dinding atau sandaran dan berhenti bila goyah.",
    "solo_advanced": "Butuh dasar yang kuat; sebaiknya dipelajari bersama pelatih.",
    "supervised_only": "Gerak pembelaan ini dipelajari sebagai pengetahuan; latihannya sebaiknya bersama pelatih.",
    "partner_required": "Membutuhkan pasangan latihan dan pelatih.",
    "restricted": "Tidak diuraikan.",
}
IMPORT_TAG = "Impor konten riset SILATARA"


class ContentError(ValueError):
    pass


# ------------------------------------------------------------------ memuat & memvalidasi berkas
@dataclass
class Bundle:
    repo: Path
    common: dict
    sources: dict[str, dict]
    movements: list[dict]
    shared: dict[str, dict]  # movement_id -> shared_context berkasnya
    files: dict[str, str]  # movement_id -> berkas asal
    courses: list[dict]
    lessons: dict[str, list[dict]]
    animations: dict[str, dict]  # movement_id -> keyframes.json


def load_bundle(repo: Path) -> Bundle:
    root = repo / "content" / "pencak-silat"
    if not root.is_dir():
        raise ContentError(f"Folder konten tidak ditemukan: {root}")
    rd = json.loads

    common = rd((root / "catalog" / "common.json").read_text())
    src = rd((repo / "research" / "pencak-silat" / "sources" / "sources.json").read_text())
    sources = {s["id"]: s for s in src["sources"]}
    movements, shared, files = [], {}, {}
    for f in sorted((root / "movements").glob("*.json")):
        data = rd(f.read_text())
        if data.get("schema") != "silatara.movements/v1":
            raise ContentError(f"{f.name}: schema tidak dikenal")
        for m in data["movements"]:
            m = dict(m)
            m["_tradition_id"] = data["tradition_id"]
            movements.append(m)
            shared[m["id"]] = data.get("shared_context", {})
            files[m["id"]] = f"content/pencak-silat/movements/{f.name}"
    courses = [rd(f.read_text()) for f in sorted((root / "curricula").glob("*.json"))]
    lessons = {}
    for f in sorted((root / "lessons").glob("*.json")):
        data = rd(f.read_text())
        lessons[data["course_id"]] = data["lessons"]
    animations = {}
    adir = root / "animations"
    if adir.is_dir():
        for d in sorted(p for p in adir.iterdir() if p.is_dir()):
            kf = d / "keyframes.json"
            if kf.exists():
                animations[d.name] = rd(kf.read_text())
    return Bundle(repo, common, sources, movements, shared, files, courses, lessons, animations)


def _resolve(m: dict, shared: dict, common: dict, node):
    """Mengganti {"ref": "shared_context.x"} / "common.safety.x" dengan isi sebenarnya."""
    if isinstance(node, dict) and set(node) == {"ref"}:
        path = node["ref"]
        if path.startswith("shared_context."):
            val = shared.get(path.split(".", 1)[1])
        else:
            val = _dig(common, path.split(".")[1:])
        if val is None:
            raise ContentError(f"{m['id']}: ref tidak ditemukan {path}")
        return val
    return node


def _dig(obj, keys):
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj


def validate_bundle(b: Bundle) -> list[str]:
    errs: list[str] = []
    trd_ids = {t["id"] for t in b.common["traditions"]}
    for t in b.common["traditions"]:
        if not ID_RE["tradition"].match(t["id"]):
            errs.append(f"tradisi: ID tidak valid {t['id']}")
        for s in t.get("source_ids", []):
            if s not in b.sources:
                errs.append(f"{t['id']}: source_id tak dikenal {s}")
    for sid in b.sources:
        if not ID_RE["source"].match(sid):
            errs.append(f"sumber: ID tidak valid {sid}")
    seen_mv, seen_ph, slugs = set(), set(), set()
    mv_ids = {m["id"] for m in b.movements}
    for m in b.movements:
        mid = m["id"]
        if not ID_RE["movement"].match(mid):
            errs.append(f"{mid}: ID gerakan tidak valid")
        if mid in seen_mv:
            errs.append(f"{mid}: ID gerakan duplikat")
        seen_mv.add(mid)
        if mid.split(".")[-1] != m["slug"]:
            errs.append(f"{mid}: slug harus sama dengan bagian akhir ID")
        key = (m["_tradition_id"], m["slug"])
        if key in slugs:
            errs.append(f"{mid}: slug duplikat dalam tradisi")
        slugs.add(key)
        if m["_tradition_id"] not in trd_ids:
            errs.append(f"{mid}: tradisi tak dikenal {m['_tradition_id']}")
        if mid.split(".")[1] != m["_tradition_id"].split(".")[1]:
            errs.append(f"{mid}: kode tradisi di ID tidak cocok dengan {m['_tradition_id']}")
        if m.get("content_status") not in CONTENT_STATUSES:
            errs.append(f"{mid}: content_status harus draft/needs_reference, bukan {m.get('content_status')!r}")
        if m.get("instructor_validation") != "not_validated":
            errs.append(f"{mid}: konten riset tidak boleh mengklaim validasi instruktur")
        if m.get("safety_class") not in SAFETY:
            errs.append(f"{mid}: safety_class tidak dikenal")
        if m.get("solo_form_status") not in SOLO_STATUS:
            errs.append(f"{mid}: solo_form_status tidak dikenal")
        if m.get("solo_form_status") != "documented_solo" and m.get("safety_class", "").startswith("solo_"):
            errs.append(f"{mid}: bentuk solo yang tidak terdokumentasi tidak boleh diberi kelas solo_*")
        if m.get("level") not in ("beginner", "intermediate", "advanced"):
            errs.append(f"{mid}: level tidak valid")
        if not m.get("references"):
            errs.append(f"{mid}: wajib memiliki rujukan")
        for r in m.get("references", []):
            if r["source_id"] not in b.sources:
                errs.append(f"{mid}: source_id tak dikenal {r['source_id']}")
            elif b.sources[r["source_id"]].get("read_status") in ("search_snippet", "unreachable"):
                errs.append(
                    f"{mid}: uraian gerak tidak boleh bersandar pada sumber {b.sources[r['source_id']]['read_status']}"
                )
        for k, v in (m.get("anatomy") or {}).items():
            if k not in ANATOMY_KEYS:
                errs.append(f"{mid}: kunci anatomi tak dikenal {k}")
            if v.get("basis") not in BASIS:
                errs.append(f"{mid}: basis anatomi tidak valid ({k})")
            for s in v.get("source_ids", []):
                if s not in b.sources:
                    errs.append(f"{mid}: source_id tak dikenal {s}")
        try:
            for part in ("context", "purpose", "meaning"):
                _resolve(m, b.shared[mid], b.common, m["cultural_context"][part])
            for vv in m["cultural_context"].get("variants", []):
                _resolve(m, b.shared[mid], b.common, vv)
        except ContentError as e:
            errs.append(str(e))
        phases = m.get("phases") or []
        if not phases:
            errs.append(f"{mid}: minimal satu fase")
        for i, ph in enumerate(phases, start=1):
            pid = ph.get("id", "")
            if pid != f"{mid}#p{i}" or ph.get("order") != i:
                errs.append(f"{mid}: fase ke-{i} harus ber-ID {mid}#p{i} dan order {i}")
            if pid in seen_ph:
                errs.append(f"{pid}: ID fase duplikat")
            seen_ph.add(pid)
            if ph.get("basis") not in BASIS:
                errs.append(f"{pid}: basis tidak valid")
            if ph.get("basis") == "source" and not ph.get("source_ids"):
                errs.append(f"{pid}: fase berbasis sumber wajib mencantumkan source_ids")
            for s in ph.get("source_ids", []):
                if s not in b.sources:
                    errs.append(f"{pid}: source_id tak dikenal {s}")
        an = m.get("animation") or {}
        if not ID_RE["animation"].match(an.get("animation_id", "")):
            errs.append(f"{mid}: animation_id tidak valid")
        spec = b.animations.get(mid)
        if b.animations:
            if spec is None:
                errs.append(f"{mid}: folder animasi tidak ada")
            else:
                if spec.get("animation_status") != an.get("status"):
                    errs.append(
                        f"{mid}: status animasi dokumen ({an.get('status')}) ≠ keyframes ({spec.get('animation_status')})"
                    )
                if spec.get("animation_id") != an.get("animation_id"):
                    errs.append(f"{mid}: animation_id dokumen ≠ keyframes")
                if an.get("status") == "generated":
                    kfs = {k["id"]: k.get("phase_id") for k in spec.get("keyframes", spec.get("markers", []))}
                    for ph in phases:
                        ref = ph.get("keyframe_ref")
                        if ref and ref not in kfs:
                            errs.append(f"{ph['id']}: keyframe_ref {ref} tidak ada di animasi")
                    for kid, pid in kfs.items():
                        if pid and pid not in {p["id"] for p in phases}:
                            errs.append(f"{mid}: keyframe {kid} menunjuk fase tak dikenal {pid}")
                elif not an.get("needs"):
                    errs.append(f"{mid}: animasi needs_reference wajib menjelaskan kebutuhan")
    # kursus & pelajaran
    for c in b.courses:
        cid = c["id"]
        if not ID_RE["course"].match(cid):
            errs.append(f"{cid}: ID kursus tidak valid")
        if c.get("tradition_id") not in trd_ids:
            errs.append(f"{cid}: tradisi tak dikenal")
        if c.get("content_status") not in CONTENT_STATUSES or c.get("instructor_validation") != "not_validated":
            errs.append(f"{cid}: status/validasi tidak sah untuk konten riset")
        mods = {m_["id"] for m_ in c["modules"]}
        for i, m_ in enumerate(c["modules"], start=1):
            if m_["id"] != f"{cid}.m{i:02d}" or m_["order"] != i:
                errs.append(f"{cid}: modul ke-{i} harus {cid}.m{i:02d}")
        ls = b.lessons.get(cid)
        if not ls:
            errs.append(f"{cid}: berkas pelajaran tidak ada")
            continue
        lslugs = set()
        for i, le in enumerate(ls, start=1):
            lid = le["id"]
            if lid != f"{cid}.l{i:02d}" or le["order"] != i:
                errs.append(f"{lid}: harus {cid}.l{i:02d} berurutan")
            if le["module_id"] not in mods:
                errs.append(f"{lid}: modul tak dikenal")
            if le["slug"] in lslugs:
                errs.append(f"{lid}: slug duplikat")
            lslugs.add(le["slug"])
            for mvid in le.get("movement_ids", []):
                if mvid not in mv_ids:
                    errs.append(f"{lid}: gerakan tak dikenal {mvid}")
                elif not mvid.startswith(f"mv.{c['tradition_id'].split('.')[1]}."):
                    errs.append(f"{lid}: gerakan {mvid} berasal dari tradisi lain (tidak boleh dicampur)")
            pm = le.get("primary_movement_id")
            if pm and pm not in le.get("movement_ids", []):
                errs.append(f"{lid}: primary_movement_id harus ada di movement_ids")
            for q in le.get("quiz", []):
                if not (0 <= q["answer_index"] < len(q["options"])):
                    errs.append(f"{lid}: kunci kuis di luar rentang")
                if q.get("source_id") not in b.sources:
                    errs.append(f"{lid}: kuis tanpa source_id yang dikenal")
            for r in le.get("references", []):
                if r["source_id"] not in b.sources:
                    errs.append(f"{lid}: source_id tak dikenal {r['source_id']}")
            for k in ("title", "description", "theory", "safety_briefing", "summary"):
                if not le.get(k):
                    errs.append(f"{lid}: bidang '{k}' kosong")
    return errs


# ------------------------------------------------------------------ komposisi teks
def _cite(b: Bundle, sid: str) -> str:
    s = b.sources[sid]
    year = s.get("year") or "t.t."
    venue = f" {s['venue']}." if s.get("venue") else ""
    return f"{s['author_or_publisher']} ({year}). {s['title']}.{venue} {s.get('url', '')}".strip()


def _citations(b: Bundle, ids) -> str:
    return "\n".join(f"- {_cite(b, s)}" for s in dict.fromkeys(ids))


def _txt(node) -> str:
    if isinstance(node, dict):
        t = node.get("text", "")
        loc = node.get("locator")
        return f"{t} ({loc})" if loc and t else t
    return str(node or "")


def movement_doc_fields(b: Bundle, m: dict) -> dict:
    sh, cm = b.shared[m["id"]], b.common
    cc = m["cultural_context"]
    res = lambda n: _resolve(m, sh, cm, n)  # noqa: E731
    ctx = [
        f"Konteks: {_txt(res(cc['context']))}",
        f"Tujuan: {_txt(res(cc['purpose']))}",
        f"Makna: {_txt(res(cc['meaning']))}",
    ]
    for v in cc.get("variants", []):
        ctx.append(f"Varian/sumber: {_txt(res(v))}")
    for d in cc.get("differs_from", []):
        ctx.append(f"Beda dengan {d['movement_id']}: {d['text']}")
    anat = m.get("anatomy") or {}
    missing = cm["anatomy_missing_text"]
    lines = []
    for k in ANATOMY_KEYS:
        v = anat.get(k)
        lines.append(f"- {ANATOMY_LABEL[k]}: {v['text']} [{v['basis']}]" if v else f"- {ANATOMY_LABEL[k]}: {missing}")
    pr = m["prerequisites"]
    prereq = (
        f"Kemampuan awal: {pr['abilities']}\nPersiapan: {pr['physical_prep']}\n"
        f"Ruang: {_dig(cm, pr['space_ref'].split('.')[1:])}\nPermukaan: {_dig(cm, pr['surface_ref'].split('.')[1:])}\n"
        f"Peralatan: {_dig(cm, pr['equipment_ref'].split('.')[1:])}\nBatasan: {_dig(cm, pr['limits_ref'].split('.')[1:])}"
    )
    pg = m["practice"]
    stop = "; ".join(_dig(cm, pg["stop_when_ref"].split(".")[1:]) or [])
    safety = (
        f"Kelas keselamatan: {m['safety_class']} · bentuk solo: {m['solo_form_status']}.\n"
        f"Mulai: {pg['start']}\nUrutan: {pg['sequence']}\nTempo: {pg['tempo']['text']} [{pg['tempo']['basis']}]\n"
        f"Pengulangan: {pg['repetitions']['text']} [{pg['repetitions']['basis']}]\nVersi lebih mudah: {pg['easier']}\n"
        f"Progresi: {pg['progression']}\nHentikan bila: {stop} ({cm['safety']['stop_basis']})\nPendinginan: {pg['cooldown']}"
    )
    terms = "; ".join(f"{t['term']} — {t['explanation']}" for t in cc.get("terminology", []))
    gaps = "; ".join(m.get("gaps", []))
    mistakes = [x["text"] if isinstance(x, dict) else str(x) for x in m.get("common_mistakes", [])]
    lm = []
    for g in m.get("landmarks", []):
        lm += [LANDMARKS[n] for n in cm["landmark_groups"][g]]
    body_parts = sorted({bp for ph in m["phases"] for bp in ph.get("body_parts", [])})
    src_ids = sorted({r["source_id"] for r in m["references"]})
    refs = "\n".join(f"- {_cite(b, r['source_id'])} — {r['locator']}: {r['supports']}" for r in m["references"])
    description = (
        "Anatomi gerakan:\n"
        + "\n".join(lines)
        + (f"\n\nRincian yang belum tercatat dalam sumber: {gaps}" if gaps else "")
        + f"\n\nRujukan:\n{refs}"
    )
    return {
        "name_id": m["names"]["primary"][:200],
        "name_local": (m["names"].get("local") or None),
        "level": m["level"],
        "safety_category": SAFETY_DB[m["safety_class"]],
        "prerequisites": prereq,
        "learning_context": "\n".join(ctx),
        "description": description,
        "terminology_notes": terms or None,
        "common_mistakes": mistakes,
        "safety_guidance": safety,
        "relevant_body_parts": body_parts,
        "relevant_landmarks": sorted(set(lm)),
        "rights_holder": None,
        "license_type": None,
        "usage_scope": USAGE_SCOPE,
        "content_basis": CONTENT_BASIS,
        "author_declaration": False,
        "source_citation": _citations(b, src_ids),
        "source_url": b.sources[src_ids[0]].get("url"),
    }


def phase_rows(m: dict) -> list[dict]:
    out = []
    for ph in m["phases"]:
        basis = ph["basis"] + (
            f" — {', '.join(ph.get('source_ids', []))} {ph.get('locator', '')}".rstrip() if ph.get("source_ids") else ""
        )
        instr = (
            f"Posisi awal: {ph['start_position']}\nPerubahan: {ph['change']}\nArah: {ph['direction']}\n"
            f"Posisi akhir: {ph['end_position']}\nBasis: {basis}"
        )
        if ph.get("mistakes"):
            instr += "\nKesalahan yang dihindari: " + "; ".join(ph["mistakes"])
        if ph.get("tempo"):
            instr += f"\nTempo: {ph['tempo']}"
        out.append(
            {
                "order_index": ph["order"] - 1,
                "name": ph["name"][:200],
                "instruction": instr,
                "body_focus": ph.get("body_parts", []),
                "safety_note": ph.get("safety"),
                "start_ms": None,
                "end_ms": None,
            }
        )
    return out


def lesson_texts(b: Bundle, c: dict, le: dict, mv_by_id: dict) -> tuple[str, str, list[dict]]:
    objective = "\n".join(f"- {o}" for o in le["objectives"])
    parts = [
        le["description"],
        f"**Kompetensi awal:** {le['prior_competence']}  \n**Durasi:** ±{le['duration_min']} menit  \n**Peralatan:** {le['equipment']}  \n**Ruang:** {le['space']}",
        f"**Keselamatan:** {le['safety_briefing']}",
    ]
    for mvid in le.get("movement_ids", []):
        m = mv_by_id[mvid]
        ph = "\n".join(f"{p['order']}. **{p['name']}** — {p['change']} → {p['end_position']}" for p in m["phases"])
        mist = "; ".join(x["text"] if isinstance(x, dict) else str(x) for x in m.get("common_mistakes", []))
        parts.append(f"### {m['names']['primary']}\n{ph}" + (f"\n\nPerhatikan: {mist}" if mist else ""))
    if le.get("practice_steps"):
        parts.append(
            "**Panduan latihan bertahap:**\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(le["practice_steps"], 1))
        )
    parts.append(f"**Rangkuman:** {le['summary']}")
    parts.append("**Refleksi:**\n" + "\n".join(f"- {r}" for r in le["reflection"]))
    body = "\n\n".join(parts)
    refs = [r["source_id"] for r in le.get("references", [])]
    for mvid in le.get("movement_ids", []):
        refs += [r["source_id"] for r in mv_by_id[mvid]["references"]]
    short = [
        f"{b.sources[r]['author_or_publisher'].split(';')[0].split(',')[0]} ({b.sources[r].get('year') or 't.t.'})"
        for r in dict.fromkeys(refs)
    ]
    attribution = ("Disusun Redaksi SILATARA berdasarkan " + "; ".join(short))[:500]
    mats = [
        {
            "kind": "text",
            "title": "Materi teori",
            "content": le["theory"],
            "attribution_text": attribution,
            "order_index": 0,
        },
        {
            "kind": "text",
            "title": "Penjelasan budaya",
            "content": le["cultural_explanation"],
            "attribution_text": attribution,
            "order_index": 1,
        },
    ]
    if le.get("quiz"):
        q = "\n\n".join(
            f"{i}. {x['q']}\n"
            + "\n".join(f"   {'ABCD'[j]}. {o}" for j, o in enumerate(x["options"]))
            + f"\n   Kunci: {'ABCD'[x['answer_index']]} (sumber: {x['source_id']})"
            for i, x in enumerate(le["quiz"], 1)
        )
        mats.append(
            {
                "kind": "text",
                "title": "Kuis pemahaman teori",
                "content": q,
                "attribution_text": attribution,
                "order_index": 2,
            }
        )
    mats.append(
        {
            "kind": "text",
            "title": "Rujukan",
            "content": "\n".join(
                f"- {_cite(b, r['source_id'])} — {r.get('locator', '')}" for r in le.get("references", [])
            ),
            "attribution_text": attribution,
            "order_index": 3,
        }
    )
    return objective, body, mats


# ------------------------------------------------------------------ penerapan ke DB
@dataclass
class Report:
    actions: list[tuple[str, str, str]] = field(default_factory=list)  # (aksi, jenis, kunci)

    def add(self, action, kind, key):
        self.actions.append((action, kind, key))

    def counts(self) -> dict:
        out: dict[str, dict[str, int]] = {}
        for a, k, _ in self.actions:
            out.setdefault(k, {}).setdefault(a, 0)
            out[k][a] += 1
        return out


def _set(row, values: dict) -> bool:
    changed = False
    for k, v in values.items():
        if getattr(row, k) != v:
            setattr(row, k, v)
            changed = True
    return changed


def _draft_note(status: str) -> str:
    return f"{IMPORT_TAG}: dasar konten source_backed (ADR-0008); status berkas '{status}'; bukan konfirmasi mitra."


def apply_bundle(db: Session, b: Bundle, operator: User | None = None) -> Report:
    rep = Report()
    uid = operator.id if operator else None
    # --- partner editorial internal
    ep = b.common["editorial_partner"]
    partner = db.scalar(select(Partner).where(Partner.slug == ep["slug"]))
    if partner is None:
        partner = Partner(
            slug=ep["slug"], name=ep["name"], partner_type=ep["partner_type"], official_description=ep["official_description"],
            verification_status="draft", status="draft", is_demo=False, public_listing_consent=False,
            review_note=f"{IMPORT_TAG}. {ep['decision_ref']}", created_by_user_id=uid,
        )  # fmt: skip
        db.add(partner)
        db.flush()
        rep.add("create", "partner", ep["slug"])
    else:
        rep.add("unchanged", "partner", ep["slug"])

    # --- tradisi
    trd_rows: dict[str, CulturalTradition] = {}
    for t in b.common["traditions"]:
        vals = {
            "name": t["name"], "local_name": t.get("local_name"), "region": t.get("region"),
            "public_summary": t["public_summary"], "access_scope": t["access_scope"],
            "source_citation": _citations(b, t["source_ids"]), "source_url": b.sources[t["source_ids"][0]].get("url"),
            "content_basis": CONTENT_BASIS,
        }  # fmt: skip
        row = db.scalar(select(CulturalTradition).where(CulturalTradition.slug == t["slug"]))
        if row is None:
            row = CulturalTradition(
                slug=t["slug"],
                status="draft",
                is_demo=False,
                review_note=_draft_note("draft"),
                created_by_user_id=uid,
                **vals,
            )
            db.add(row)
            db.flush()
            rep.add("create", "tradition", t["id"])
        elif not _can_update(row):
            rep.add("protected", "tradition", t["id"])
        else:
            rep.add("update" if _set(row, vals) else "unchanged", "tradition", t["id"])
        trd_rows[t["id"]] = row
        if not db.scalar(
            select(TraditionPartner).where(
                TraditionPartner.tradition_id == row.id, TraditionPartner.partner_id == partner.id
            )
        ):
            db.add(TraditionPartner(tradition_id=row.id, partner_id=partner.id, relationship_type="research_partner"))
            db.flush()

    # --- gerakan + dokumen + fase
    mv_rows: dict[str, Movement] = {}
    for m in b.movements:
        trd = trd_rows[m["_tradition_id"]]
        doc_vals = movement_doc_fields(b, m)
        phases = phase_rows(m)
        mvals = {
            "name_id": doc_vals["name_id"], "name_local": doc_vals["name_local"],
            "description": _txt(_resolve(m, b.shared[m["id"]], b.common, m["cultural_context"]["purpose"])) or None,
            "safety_notes": SAFETY_TEXT[m["safety_class"]],
            "content_basis": CONTENT_BASIS,
            "practice_mode": "not_for_practice", "assessment_enabled": False,
            "level": m["level"], "safety_category": doc_vals["safety_category"],
            "source_citation": doc_vals["source_citation"], "source_url": doc_vals["source_url"],
            "review_note": _draft_note(m["content_status"]),
        }  # fmt: skip
        row = db.scalar(select(Movement).where(Movement.tradition_id == trd.id, Movement.slug == m["slug"]))
        if row is None:
            row = Movement(
                tradition_id=trd.id,
                partner_id=partner.id,
                slug=m["slug"],
                status="draft",
                is_demo=False,
                created_by_user_id=uid,
                **mvals,
            )
            db.add(row)
            db.flush()
            rep.add("create", "movement", m["id"])
        elif not _can_update(row):
            rep.add("protected", "movement", m["id"])
        else:
            rep.add("update" if _set(row, mvals) else "unchanged", "movement", m["id"])
        mv_rows[m["id"]] = row
        _apply_document(db, rep, row, m, doc_vals, phases, uid)

    # --- kursus, modul, pelajaran, materi
    mv_by_id = {m["id"]: m for m in b.movements}
    for c in b.courses:
        cvals = {
            "tradition_id": trd_rows[c["tradition_id"]].id, "partner_id": partner.id, "title": c["title"], "summary": c["summary"],
            "level": c["level"], "estimated_minutes": c["estimated_minutes"], "safety_notes": c["safety_notes"],
            "source_citation": _citations(b, c["source_ids"]), "source_url": b.sources[c["source_ids"][0]].get("url"),
            "review_note": _draft_note(c["content_status"]) + " " + c.get("editorial_note", ""),
            "content_basis": CONTENT_BASIS,
        }  # fmt: skip
        crow = db.scalar(select(Course).where(Course.slug == c["slug"]))
        if crow is None:
            crow = Course(
                slug=c["slug"],
                status="draft",
                is_demo=False,
                distribution_scope="public",
                created_by_user_id=uid,
                **cvals,
            )
            db.add(crow)
            db.flush()
            rep.add("create", "course", c["id"])
        elif not _can_update(crow):
            rep.add("protected", "course", c["id"])
            continue
        else:
            rep.add("update" if _set(crow, cvals) else "unchanged", "course", c["id"])
        mod_rows = {}
        for mod in c["modules"]:
            mr = db.scalar(
                select(CourseModule).where(CourseModule.course_id == crow.id, CourseModule.order_index == mod["order"])
            )
            mvals2 = {"title": mod["title"], "summary": mod["summary"]}
            if mr is None:
                mr = CourseModule(course_id=crow.id, order_index=mod["order"], **mvals2)
                db.add(mr)
                db.flush()
                rep.add("create", "module", mod["id"])
            else:
                rep.add("update" if _set(mr, mvals2) else "unchanged", "module", mod["id"])
            mod_rows[mod["id"]] = mr
        for le in b.lessons[c["id"]]:
            objective, body, mats = lesson_texts(b, c, le, mv_by_id)
            lvals = {
                "module_id": mod_rows[le["module_id"]].id, "title": le["title"], "objective": objective, "body": body,
                "safety_notes": le["safety_briefing"], "order_index": le["order"], "estimated_minutes": le["duration_min"],
                "movement_id": mv_rows[le["primary_movement_id"]].id if le.get("primary_movement_id") else None,
                "source_citation": _citations(b, [r["source_id"] for r in le["references"]]),
                "source_url": b.sources[le["references"][0]["source_id"]].get("url") if le["references"] else None,
                "review_note": _draft_note("draft"),
                "content_basis": CONTENT_BASIS,
            }  # fmt: skip
            lr = db.scalar(select(Lesson).where(Lesson.course_id == crow.id, Lesson.slug == le["slug"]))
            if lr is None:
                lr = Lesson(
                    course_id=crow.id, slug=le["slug"], status="draft", is_demo=False, created_by_user_id=uid, **lvals
                )
                db.add(lr)
                db.flush()
                rep.add("create", "lesson", le["id"])
            elif not _can_update(lr):
                rep.add("protected", "lesson", le["id"])
                continue
            else:
                rep.add("update" if _set(lr, lvals) else "unchanged", "lesson", le["id"])
            existing = db.scalars(
                select(LessonMaterial).where(LessonMaterial.lesson_id == lr.id).order_by(LessonMaterial.order_index)
            ).all()
            cur = [(x.kind, x.title, x.content, x.attribution_text, x.order_index) for x in existing]
            new = [(x["kind"], x["title"], x["content"], x["attribution_text"], x["order_index"]) for x in mats]
            if cur != new:
                for x in existing:
                    db.delete(x)
                db.flush()
                for x in mats:
                    db.add(LessonMaterial(lesson_id=lr.id, url=None, permission_ref=None, **x))
                db.flush()
                rep.add("replace" if existing else "create", "lesson_materials", le["id"])
            else:
                rep.add("unchanged", "lesson_materials", le["id"])
    db.flush()
    return rep


def _apply_document(db, rep, mv: Movement, m: dict, vals: dict, phases: list[dict], uid):
    docs = db.scalars(
        select(MovementDocument)
        .where(MovementDocument.movement_id == mv.id, MovementDocument.deleted_at.is_(None))
        .order_by(MovementDocument.version_no.desc())
    ).all()
    latest = docs[0] if docs else None
    if latest is not None and latest.status in ("pending_review", "verified"):
        rep.add("blocked_review", "movement_document", m["id"])
        return
    if latest is not None and latest.status in EDITABLE:
        old = db.scalars(
            select(MovementPhase).where(MovementPhase.document_id == latest.id).order_by(MovementPhase.order_index)
        ).all()
        cur_ph = [{k: getattr(p, k) for k in phases[0]} for p in old] if phases else []
        changed = _set(latest, {**vals, "changelog": latest.changelog})  # changelog tidak ditimpa
        if cur_ph != phases:
            for p in old:
                db.delete(p)
            db.flush()
            for p in phases:
                db.add(MovementPhase(document_id=latest.id, **p))
            changed = True
        if changed:
            latest.changelog = f"{IMPORT_TAG}: pembaruan isi draf v{latest.version_no}."
        db.flush()
        rep.add("update" if changed else "unchanged", "movement_document", m["id"])
        return
    # tidak ada versi, atau versi terakhir published/archived → buat versi draf baru
    if latest is not None:
        last_ph = db.scalars(
            select(MovementPhase).where(MovementPhase.document_id == latest.id).order_by(MovementPhase.order_index)
        ).all()
        same = (
            all(getattr(latest, k) == v for k, v in vals.items())
            and [{k: getattr(p, k) for k in phases[0]} for p in last_ph] == phases
        )
        if same:
            rep.add("unchanged", "movement_document", m["id"])
            return
    nxt = (
        db.scalar(select(func.max(MovementDocument.version_no)).where(MovementDocument.movement_id == mv.id)) or 0
    ) + 1
    d = MovementDocument(
        movement_id=mv.id, version_no=nxt, status="draft", is_demo=False, legacy_import=False, created_by_user_id=uid,
        changelog=f"{IMPORT_TAG}: versi {nxt} dibuat dari berkas konten (validasi instruktur: belum).", **vals,
    )  # fmt: skip
    db.add(d)
    db.flush()
    for p in phases:
        db.add(MovementPhase(document_id=d.id, **p))
    db.flush()
    rep.add("create" if latest is None else "new_version", "movement_document", m["id"])


def publish_editorial(db: Session, b: Bundle, operator: User, rep: Report) -> None:
    """Terbitkan pengetahuan berbasis sumber lewat tinjauan editorial (ADR-0008). Tidak menyentuh konfirmasi mitra,
    tidak membuka Practice Studio (practice_mode tetap not_for_practice), dan tidak menyentuh konten non-impor."""
    from datetime import UTC, datetime

    t = datetime.now(UTC)
    appr = {"approved_by_user_id": operator.id, "approved_at": t, "approval_evidence_ref": EDITORIAL_EVIDENCE}

    def pub(row, kind, key, extra=None):
        if not (row.content_basis == CONTENT_BASIS and (row.review_note or "").startswith(IMPORT_TAG)):
            rep.add("skip_not_import", kind, key)
            return
        if row.status == "published":
            rep.add("already_published", kind, key)
            return
        for k, v in {**appr, **(extra or {}), "status": "published", "published_at": t}.items():
            setattr(row, k, v)
        rep.add("publish", kind, key)

    for tdef in b.common["traditions"]:
        row = db.scalar(select(CulturalTradition).where(CulturalTradition.slug == tdef["slug"]))
        pub(row, "tradition", tdef["id"], {"access_scope": "public"})
    db.flush()
    for m in b.movements:
        trd = db.scalar(
            select(CulturalTradition).where(
                CulturalTradition.slug
                == next(x["slug"] for x in b.common["traditions"] if x["id"] == m["_tradition_id"])
            )
        )
        mv = db.scalar(select(Movement).where(Movement.tradition_id == trd.id, Movement.slug == m["slug"]))
        docs = db.scalars(
            select(MovementDocument)
            .where(MovementDocument.movement_id == mv.id, MovementDocument.deleted_at.is_(None))
            .order_by(MovementDocument.version_no.desc())
        ).all()
        latest = docs[0]
        if latest.status != "published":
            if latest.status in ("pending_review", "verified"):
                rep.add("blocked_review", "movement_document", m["id"])
                continue
            for old in docs[1:]:
                if old.status == "published":
                    old.status = "archived"
            db.flush()
            for k, v in {
                **appr,
                "curator_reviewed_by_user_id": operator.id,
                "curator_reviewed_at": t,
                "status": "published",
                "published_at": t,
            }.items():
                setattr(latest, k, v)
            db.flush()
            rep.add("publish", "movement_document", m["id"])
        else:
            rep.add("already_published", "movement_document", m["id"])
        pub(mv, "movement", m["id"])
        mv.published_document_id, mv.published_version_no = latest.id, latest.version_no
        mv.practice_mode, mv.assessment_enabled = "not_for_practice", False
        db.flush()
    for c in b.courses:
        crow = db.scalar(select(Course).where(Course.slug == c["slug"]))
        pub(crow, "course", c["id"], {"distribution_scope": "public"})
        for le in b.lessons[c["id"]]:
            lr = db.scalar(select(Lesson).where(Lesson.course_id == crow.id, Lesson.slug == le["slug"]))
            pub(lr, "lesson", le["id"])
    db.flush()


def run_import(
    db: Session, repo: Path, *, execute: bool, operator_email: str | None = None, publish: bool = False
) -> dict:
    b = load_bundle(repo)
    errs = validate_bundle(b)
    if errs:
        raise ContentError("Validasi konten gagal:\n" + "\n".join(errs))
    operator = None
    if operator_email:
        operator = db.scalar(select(User).where(User.email == operator_email.lower()))
        if operator is None or operator.role not in ("admin", "curator"):
            raise ContentError("--operator harus akun admin/kurator yang ada")
    if publish and (operator is None or operator.email.endswith("@silatara.test")):
        raise ContentError("--publish wajib --operator akun redaksi (admin/kurator) yang BUKAN akun demo")
    rep = apply_bundle(db, b, operator)
    if publish:
        publish_editorial(db, b, operator, rep)
    published = db.scalar(
        select(func.count())
        .select_from(Movement)
        .where(Movement.review_note.like(f"{IMPORT_TAG}%"), Movement.status == "published")
    )
    summary = {
        "mode": "EXECUTE" if execute else "DRY-RUN",
        "publish": publish,
        "counts": rep.counts(),
        "published_import_movements": published,
    }
    if execute:
        audit.record(
            db,
            actor=operator,
            action="content.publish_editorial" if publish else "content.import",
            entity_type="content_bundle",
            entity_id="pencak-silat",
            detail=summary["counts"],
        )
        db.commit()
    else:
        db.rollback()
    return summary
