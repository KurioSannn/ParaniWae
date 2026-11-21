"""Validasi teknis aset animasi SILATARA (stdlib).

Memeriksa: SVG valid (XML), viewBox konsisten dengan rig, tanpa URL/skrip eksternal, semua animasi ber-ID dan
menunjuk movement_id yang benar, keyframe lengkap, timing valid, loop kembali ke pose awal, ukuran wajar,
manifest konsisten (hash), dan tidak ada bagian tubuh keluar kanvas (clipping).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import silat_anim as sa  # noqa: E402

SVG_NS = "{http://www.w3.org/2000/svg}"
MAX_SVG_BYTES = 250_000
ID_RE = re.compile(r"^anim\.[a-z0-9-]+\.[a-z0-9-]+\.v\d+$")
MV_RE = re.compile(r"^mv\.[a-z0-9-]+\.[a-z0-9-]+$")
PHASE_RE = re.compile(r"^mv\.[a-z0-9-]+\.[a-z0-9-]+#p\d+$")
FORBIDDEN = re.compile(r"(<script|javascript:|https?://(?!www\.w3\.org/2000/svg)|xlink:href|\bhref=|@import|url\(|<foreignObject|<image)", re.I)
REQUIRED_POSE_KEYS = {"pelvis", "feet", "arms"}


def _check_svg(path: Path, rig: dict, spec: dict, errors: list[str], *, animated: bool):
    raw = path.read_bytes()
    if len(raw) > MAX_SVG_BYTES:
        errors.append(f"{path.name}: {len(raw)} byte > batas {MAX_SVG_BYTES}")
    txt = raw.decode("utf-8")
    m = FORBIDDEN.search(txt)
    if m:
        errors.append(f"{path.name}: konten terlarang/eksternal ditemukan: {m.group(0)!r}")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        errors.append(f"{path.name}: XML tidak valid: {e}")
        return
    if root.tag != f"{SVG_NS}svg":
        errors.append(f"{path.name}: elemen akar bukan <svg>")
    W, H = rig["canvas"]["width"], rig["canvas"]["height"]
    if root.get("viewBox") != f"0 0 {W} {H}":
        errors.append(f"{path.name}: viewBox {root.get('viewBox')!r} != '0 0 {W} {H}'")
    if root.get("data-movement-id") != spec["movement_id"]:
        errors.append(f"{path.name}: data-movement-id tidak cocok")
    expect_id = spec["animation_id"] + ("" if animated else "-thumb")
    if root.get("id") != expect_id:
        errors.append(f"{path.name}: id akar {root.get('id')!r} != {expect_id!r}")
    if root.find(f"{SVG_NS}title") is None or root.find(f"{SVG_NS}desc") is None:
        errors.append(f"{path.name}: <title>/<desc> wajib ada (aksesibilitas)")
    anims = [el for el in root.iter() if el.tag in (f"{SVG_NS}animate", f"{SVG_NS}animateTransform", f"{SVG_NS}set")]
    if animated and not anims:
        errors.append(f"{path.name}: tidak ada elemen animasi — bukan animasi bergerak")
    if not animated and anims:
        errors.append(f"{path.name}: thumbnail tidak boleh beranimasi")
    durs = set()
    for el in anims:
        if el.get("repeatCount") != "indefinite":
            errors.append(f"{path.name}: animasi tanpa repeatCount=indefinite (tidak loop)")
        d = el.get("dur", "")
        if not re.fullmatch(r"\d+(\.\d+)?s", d) or float(d[:-1]) <= 0:
            errors.append(f"{path.name}: dur tidak valid {d!r}")
        durs.add(d)
        vals = (el.get("values") or "").split(";")
        kt = el.get("keyTimes")
        if kt is not None:
            ks = [float(x) for x in kt.split(";")]
            if ks[0] != 0 or any(b < a for a, b in zip(ks, ks[1:], strict=False)) or ks[-1] > 1:
                errors.append(f"{path.name}: keyTimes tidak monoton/0..1")
            if len(ks) != len(vals):
                errors.append(f"{path.name}: jumlah keyTimes != values")
            if el.get("calcMode") not in ("discrete",) and ks[-1] != 1:
                errors.append(f"{path.name}: keyTimes non-diskret wajib berakhir di 1")
        if el.get("calcMode", "linear") == "linear" and len(vals) >= 2 and vals[0] != vals[-1]:
            errors.append(f"{path.name}: animasi linear tidak kembali ke nilai awal (loop terputus): {vals[0]} vs {vals[-1]}")
    if len(durs) > 1:
        errors.append(f"{path.name}: dur berbeda-beda antar elemen {sorted(durs)} — loop tidak sinkron")
    ids = [el.get("id") for el in root.iter() if el.get("id")]
    if len(ids) != len(set(ids)):
        errors.append(f"{path.name}: id duplikat")


def validate_dir(anim_dir: Path, rig_path: Path, phase_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    rig = json.loads(rig_path.read_text())
    kf_path = anim_dir / "keyframes.json"
    if not kf_path.exists():
        return [f"{anim_dir.name}: keyframes.json tidak ada"]
    spec = json.loads(kf_path.read_text())
    status = spec.get("animation_status")
    if not MV_RE.match(spec.get("movement_id", "")) or spec["movement_id"] != anim_dir.name:
        errors.append(f"{anim_dir.name}: movement_id {spec.get('movement_id')!r} harus sama dengan nama folder")
    if not ID_RE.match(spec.get("animation_id", "")):
        errors.append(f"{anim_dir.name}: animation_id tidak sesuai pola")
    if not (anim_dir / "ANIMATION_NOTES.md").exists():
        errors.append(f"{anim_dir.name}: ANIMATION_NOTES.md wajib ada")
    if status == "needs_reference":
        if not spec.get("needs"):
            errors.append(f"{anim_dir.name}: needs_reference wajib menjelaskan 'needs'")
        for f in ("animation.svg", "thumbnail.svg"):
            if (anim_dir / f).exists():
                errors.append(f"{anim_dir.name}: {f} tidak boleh ada untuk status needs_reference")
        return errors
    if status != "generated":
        return errors + [f"{anim_dir.name}: animation_status tidak dikenal {status!r}"]
    for f in ("animation.svg", "thumbnail.svg", "rig.json", "animation-manifest.json"):
        if not (anim_dir / f).exists():
            errors.append(f"{anim_dir.name}: {f} tidak ada — jalankan build")
    if errors:
        return errors
    man = json.loads((anim_dir / "animation-manifest.json").read_text())
    if man["movement_id"] != spec["movement_id"] or man["animation_id"] != spec["animation_id"]:
        errors.append(f"{anim_dir.name}: manifest tidak cocok dengan keyframes")
    if man["keyframes_sha256"] != hashlib.sha256(kf_path.read_bytes()).hexdigest():
        errors.append(f"{anim_dir.name}: keyframes berubah sejak build (hash manifest kedaluwarsa)")
    if man["svg_sha256"] != hashlib.sha256((anim_dir / "animation.svg").read_bytes()).hexdigest():
        errors.append(f"{anim_dir.name}: animation.svg berbeda dari manifest")
    _check_svg(anim_dir / "animation.svg", rig, spec, errors, animated=True)
    _check_svg(anim_dir / "thumbnail.svg", rig, spec, errors, animated=False)

    # keyframe lengkap & fase
    items = spec.get("keyframes") or spec.get("markers") or []
    seen = set()
    for kf in items:
        if not re.fullmatch(r"kf-\d+", kf.get("id", "")):
            errors.append(f"{anim_dir.name}: id keyframe tidak valid {kf.get('id')!r}")
        if kf["id"] in seen:
            errors.append(f"{anim_dir.name}: id keyframe duplikat {kf['id']}")
        seen.add(kf["id"])
        pid = kf.get("phase_id")
        if pid is not None:
            if not PHASE_RE.match(pid) or not pid.startswith(spec["movement_id"] + "#"):
                errors.append(f"{anim_dir.name}: phase_id {pid!r} bukan milik gerakan ini")
            elif phase_ids is not None and pid not in phase_ids:
                errors.append(f"{anim_dir.name}: phase_id {pid!r} tidak ada di dokumen gerakan")
        if spec["view"] != "top":
            missing = REQUIRED_POSE_KEYS - set(kf.get("pose", {}))
            if missing:
                errors.append(f"{anim_dir.name}: {kf['id']} pose tidak lengkap, kurang {sorted(missing)}")
            if not kf.get("label"):
                errors.append(f"{anim_dir.name}: {kf['id']} label kosong")
    if spec["view"] == "top":
        W, m = rig["canvas"]["width"], rig["canvas"]["margin"]
        texts = [(g["at"][0], g["text"], g.get("size", 11)) for g in spec.get("guides", []) if g["type"] == "label"]
        texts += [(W / 2, spec.get("legend", ""), 10), (W / 2, spec["title"], 15)]
        for x, t, size in texts:
            half = len(t) * size * 0.29  # perkiraan lebar huruf sans-serif
            if x - half < m or x + half > W - m:
                errors.append(f"{anim_dir.name}: teks '{t[:30]}' kemungkinan terpotong tepi kanvas")
        for mk in items:
            x, y = mk["pos"]
            if not (m + 17 <= x <= W - m - 17 and 50 <= y <= rig["canvas"]["height"] - 40):
                errors.append(f"{anim_dir.name}: penanda {mk['id']} di luar area aman")
    if spec["view"] != "top":
        try:
            frames, total, segs = sa.sample(rig, spec)
        except sa.AnimationError as e:
            return errors + [f"{anim_dir.name}: {e}"]
        if total < 1500 or total > 30000:
            errors.append(f"{anim_dir.name}: durasi {total}ms di luar rentang nyaman 1,5–30 dtk")
        ik = max(fr.ik_error for fr in frames)
        if ik > sa.IK_TOLERANCE_PX:
            errors.append(f"{anim_dir.name}: kaki tidak menjangkau target (galat IK {ik:.2f}px) — pose melayang/terentang")
        m = rig["canvas"]["margin"]
        x0, y0, x1, y1 = sa.frame_bounds(rig, frames)
        W, H = rig["canvas"]["width"], rig["canvas"]["height"]
        if x0 < m or y0 < 50 or x1 > W - m or y1 > H - m:
            errors.append(f"{anim_dir.name}: tubuh keluar area aman kanvas (bounds {x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f})")
        first = sa.full_pose(next(k for k in items if k["id"] == spec["sequence"][0]["pose"])["pose"])
        if _rounded(first) != _rounded(frames[-1].pose):
            errors.append(f"{anim_dir.name}: frame terakhir tidak sama dengan pose awal — loop akan melompat")
        used = {s["pose"] for s in spec["sequence"]}
        unused = seen - used
        if unused:
            errors.append(f"{anim_dir.name}: keyframe tidak dipakai di sequence: {sorted(unused)}")
    return errors


def _rounded(v):
    if isinstance(v, float):
        return round(v, 3)
    if isinstance(v, list):
        return [_rounded(x) for x in v]
    if isinstance(v, dict):
        return {k: _rounded(x) for k, x in v.items()}
    return v


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path("content/pencak-silat/animations")
    rig_path = Path(__file__).resolve().parent / "rig.json"
    movements_dir = root.parent / "movements"
    phases = _phase_index(movements_dir) if movements_dir.exists() else None
    bad = 0
    dirs = sorted(p for p in root.iterdir() if p.is_dir())
    for d in dirs:
        errs = validate_dir(d, rig_path, phases)
        if errs:
            bad += 1
            for e in errs:
                print("ERROR", e)
    print(f"{len(dirs)} folder animasi diperiksa, {bad} bermasalah")
    return 1 if bad else 0


def _phase_index(movements_dir: Path) -> set[str]:
    ids = set()
    for f in movements_dir.glob("*.json"):
        data = json.loads(f.read_text())
        for mv in data.get("movements", []):
            for ph in mv.get("phases", []):
                ids.add(ph["id"])
    return ids


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
