"""Kesiapan penilaian per gerakan -> content/pencak-silat/assessments/readiness.json (hanya pustaka standar).

Alasan 'belum siap' diturunkan dari data, bukan dikarang: kategori gerak, status gerak solo, status peraga 3D,
dan ada/tidaknya parameter terukur di dokumen gerakan.
"""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
C = ROOT / "content/pencak-silat"


def main():
    clips = {c["movement_id"]: c for c in json.loads((C / "character/clips.json").read_text())["clips"]}
    val = {c["movement_id"]: c["ok"] for c in json.loads((C / "character/validation.json").read_text())["clips"]}
    protos = {}
    for f in glob.glob(str(C / "assessments/*.protocol.json")):
        p = json.loads(Path(f).read_text())
        protos[p["movement_id"]] = p
    out = []
    for f in sorted(glob.glob(str(C / "movements/*.json"))):
        d = json.loads(Path(f).read_text())
        for m in d["movements"] if isinstance(d, dict) else d:
            mid = m["id"]
            has3d = mid in clips and val.get(mid, False)
            if mid in protos:
                status, reason = "active", f"Protokol {protos[mid]['protocol_version']} aktif ({len(protos[mid]['criteria'])} kriteria)."
            elif m.get("safety_class") != "solo_beginner":
                status, reason = "not_ready", "Bukan gerak solo tingkat pemula; latihan dengan kamera tidak dibuka (aturan keselamatan)."
            elif m.get("solo_form_status") != "documented_solo":
                status, reason = "not_ready", "Bentuk latihan solo tidak terdokumentasi di sumber; latih bersama pelatih."
            elif m["category"] in ("pola_langkah", "arah_langkah"):
                status, reason = "not_ready", "Pola/arah langkah diukur di lantai (tampak atas); kamera depan/samping tidak dapat mengukurnya dengan andal."
            elif m["category"] == "sikap_duduk":
                status, reason = "not_ready", "Belum ada peraga referensi untuk sikap duduk."
            elif not has3d:
                status, reason = "not_ready", "Belum ada peraga 3D yang lolos pemeriksaan untuk dijadikan referensi."
            else:
                status, reason = "candidate", "Peraga 3D tersedia; parameter terukur dari sumber belum disusun menjadi protokol."
            out.append({"movement_id": mid, "name": m["names"]["primary"], "category": m["category"], "has_3d": has3d,
                        "assessment_status": status, "reason": reason})
    doc = {"schema": "silatara.assessment-readiness/v1", "movements": out,
           "summary": {s: sum(1 for x in out if x["assessment_status"] == s) for s in ("active", "candidate", "not_ready")}}
    (C / "assessments/readiness.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(doc["summary"]))


if __name__ == "__main__":
    main()
