"""Bangun karakter + semua klip + referensi + laporan validasi.

Pemakaian (dari akar repo): docker run --rm -u $(id -u):$(id -g) -v "$PWD":/repo silatara-character-tools:1 tools/character/build_all.py
Keluaran: content/pencak-silat/character/{silatara-instructor.glb, character.json, clips.json, validation.json, reference/*.json}
"""
from __future__ import annotations

import hashlib
import os
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import animate as an  # noqa: E402
import build_character as bc  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ANIM = ROOT / "content/pencak-silat/animations"
OUT = Path(os.environ["CHAR_OUT"]) if os.environ.get("CHAR_OUT") else ROOT / "content/pencak-silat/character"
ONLY = set(filter(None, os.environ.get("CHAR_CLIPS", "").split(",")))  # pratinjau cepat: subset klip (gunakan CHAR_OUT terpisah)
REF_FPS = 15
VIEW_REC = {"side": "samping", "front": "depan"}


def lbs(mesh, frame, J, names, rest_pos, sel):
    """Linear blend skinning numpy untuk subset verteks (validasi tembus lantai/badan)."""
    P = mesh["pos"][sel]
    jn, wt = mesh["jnt"][sel].astype(int), mesh["wgt"][sel].astype(float) / 255.0
    out = np.zeros_like(P)
    for k in range(4):
        idx = jn[:, k]
        w = wt[:, k][:, None]
        Gs = np.stack([frame["G"][names[i]] for i in idx])
        bp = np.stack([frame["pos"][names[i]] for i in idx])
        rp = np.stack([rest_pos[names[i]] for i in idx])
        out += w * (np.einsum("nij,nj->ni", Gs, P - rp) + bp)
    return out


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reference").mkdir(exist_ok=True)
    J = bc.build_rig()
    names = list(J.keys())
    an.J_TAIL.update({k: j.tail for k, j in J.items()})
    an.J_POS.update({k: j.pos for k, j in J.items()})
    poser = an.Poser(J)
    rest_pos = {k: j.pos for k, j in J.items()}
    meshes = bc.build_meshes(J)
    print(f"mesh: {sum(len(m['pos']) for m in meshes)} verteks, {sum(len(m['idx']) for m in meshes)} segitiga ({time.time() - t0:.1f}s)", flush=True)

    feet_sel = {m["name"]: np.where(m["pos"][:, 1] < 0.12)[0] for m in meshes if m["name"] == "skin_body"}
    hand_sel = {m["name"]: np.arange(0, len(m["pos"]), 12) for m in meshes if m["name"].startswith("hand_")}
    mesh_by = {m["name"]: m for m in meshes}

    specs = []
    for d in sorted(ANIM.iterdir()):
        kf = d / "keyframes.json"
        if not kf.exists():
            continue
        s = json.loads(kf.read_text(encoding="utf-8"))
        if s.get("animation_status") == "generated" and s.get("view") in ("side", "front") and (not ONLY or s["movement_id"] in ONLY):
            specs.append(s)
    idle = {"movement_id": "idle", "animation_id": "anim.idle.v1", "title": "Sikap siap (diam)", "view": "front", "source_ids": [],
            "keyframes": [{"id": "i1", "label": "Siap", "pose": {"arms": {"L": [10, 6], "R": [10, 6]}, "hands": {"L": "open", "R": "open"}}},
                          {"id": "i2", "label": "Siap", "pose": {"arms": {"L": [11, 8], "R": [11, 8]}, "head": 1.5, "hands": {"L": "open", "R": "open"}}}],
            "sequence": [{"pose": "i1", "hold_ms": 600}, {"pose": "i2", "move_ms": 1600, "hold_ms": 300}], "return_ms": 1600}
    clips, anims, report = [], [], {"clips": [], "generated_at": time.strftime("%Y-%m-%d"), "character_version": bc.CHARACTER_VERSION}
    for spec in [idle] + specs:
        c = an.build_clip(poser, spec)
        fr = c["frames"]
        # ---- validasi
        ik_err, slide, floor_min, pen, knee_max, elbow_max, arm_gap = 0.0, 0.0, 9.0, 0, 0.0, 0.0, 9.0
        for i, f in enumerate(fr):
            for s in ("L", "R"):
                ik_err = max(ik_err, float(np.linalg.norm(f["pos"][f"Foot.{s}"] - f["targets"]["ankles"][s])))
                if i and np.allclose(f["targets"]["ankles"][s], fr[i - 1]["targets"]["ankles"][s]) and f["targets"]["ankles"][s][1] <= bc.ANKLE_Y + 1e-6:
                    slide = max(slide, float(np.linalg.norm(f["pos"][f"Foot.{s}"] - fr[i - 1]["pos"][f"Foot.{s}"])))
                th = f["pos"][f"LowerLeg.{s}"] - f["pos"][f"UpperLeg.{s}"]
                sh = f["pos"][f"Foot.{s}"] - f["pos"][f"LowerLeg.{s}"]
                knee_max = max(knee_max, math.degrees(math.acos(np.clip(np.dot(th, sh) / np.linalg.norm(th) / np.linalg.norm(sh), -1, 1))))
                ua = f["pos"][f"LowerArm.{s}"] - f["pos"][f"UpperArm.{s}"]
                fa = f["pos"][f"Hand.{s}"] - f["pos"][f"LowerArm.{s}"]
                elbow_max = max(elbow_max, math.degrees(math.acos(np.clip(np.dot(ua, fa) / np.linalg.norm(ua) / np.linalg.norm(fa), -1, 1))))
            arm_gap = min(arm_gap, an.seg_seg_dist(f["pos"]["LowerArm.L"], f["pos"]["Hand.L"], f["pos"]["LowerArm.R"], f["pos"]["Hand.R"]))
            if i % 3 == 0:
                fv = lbs(mesh_by["skin_body"], f, J, names, rest_pos, feet_sel["skin_body"])
                floor_min = min(floor_min, float(fv[:, 1].min()))
                Ri = f["G"]["Chest"].T
                for hn, sel in hand_sel.items():
                    hv = lbs(mesh_by[hn], f, J, names, rest_pos, sel)
                    hv_local = (Ri @ (hv - f["hips"]).T).T + np.array([0, bc.HIP_Y, 0])  # putar terhadap pinggul
                    pen += int(sum(an.torso_sdf(p) < -0.012 for p in hv_local))
        loop_q = max(float(np.max(np.abs(an.mat_to_quat(fr[0]["G"][b]) - an.mat_to_quat(fr[-1]["G"][b])))) for b in names)
        unresolved = [n for n in c["notes"] if n.get("correction") == "tidak_terselesaikan" or n["type"] == "arm_keyframe_unresolved"]
        checks = {
            "ik_error_max_mm": round(ik_err * 1000, 2), "planted_foot_slide_max_mm": round(slide * 1000, 3),
            "floor_min_mm": round(floor_min * 1000, 2), "hand_torso_penetration_vertices": pen,
            "knee_flex_max_deg": round(knee_max, 1), "elbow_flex_max_deg": round(elbow_max, 1),
            "loop_closure_quat_maxdiff": round(loop_q, 6), "ik_clamps": sum(1 for n in c["notes"] if n["type"] == "ik_clamp"),
            "forearm_gap_min_mm": round(arm_gap * 1000, 1),
            "arm_keyframes": [n for n in c["notes"] if n["type"] == "arm_keyframe"],
            "arm_frame_corrections": len([n for n in c["notes"] if n["type"] == "arm_clearance"]),
            "arm_clearance_unresolved": len(unresolved),
        }
        ok = (ik_err < 0.005 and slide < 0.003 and floor_min > -0.006 and pen == 0 and knee_max < 150 and elbow_max < 160
              and loop_q < 1e-3 and not unresolved and arm_gap > 0.05)
        tracks = an.tracks_from_frames(poser, fr)
        meta = {
            "movement_id": spec["movement_id"], "clip": spec["movement_id"], "animation_id": spec["animation_id"].replace(".v1", ".3d.v1"),
            "source_animation_id": spec["animation_id"], "title": spec.get("title"), "duration_s": round(c["duration"], 3),
            "loop_interval_s": round(c["duration"], 3), "view_recommendation": VIEW_REC.get(c["view"], "depan"),
            "source_view": c["view"], "phases": c["phases"], "source_ids": spec.get("source_ids", []),
            "validation_status": "generated_checked" if ok else "generated_needs_fix",
            "interpretation": "Tafsir editorial atas uraian sumber; bukan rekaman gerak instruktur. Belum ditinjau instruktur.",
        }
        anims.append({"name": spec["movement_id"], "tracks": tracks, "extras": {"phases": c["phases"], "duration_s": meta["duration_s"]}})
        clips.append(meta)
        report["clips"].append({"movement_id": spec["movement_id"], "ok": ok, **checks, "keys": int(sum(len(t["times"]) for t in tracks))})
        # ---- referensi landmark (untuk penilaian)
        if spec["movement_id"] != "idle":
            step = max(1, round(an.FPS / REF_FPS))
            seq = []
            for f in fr[::step]:
                lm, hands = an.landmarks(f["pos"], f["G"])
                seq.append({"t": round(f["t"], 3), "keyframe": f["kf"],
                            "pose": [[round(float(x), 4) for x in p] for p in lm],
                            "hands": {s: [[round(float(x), 4) for x in p] for p in hands[s]] for s in ("L", "R")}})
            ref = {"schema": "silatara.reference-sequence/v1", "movement_id": spec["movement_id"],
                   "reference_id": f"ref.{spec['movement_id']}.3d.v1", "animation_id": meta["animation_id"],
                   "coordinate_system": "meter; Y ke atas; karakter menghadap +Z; sisi kiri karakter = +X; indeks MediaPipe Pose (33) & Hand (21)",
                   "fps": REF_FPS, "view": c["view"], "phases": c["phases"], "frames": seq,
                   "provenance": "Dihitung dari klip 3D SILATARA (tafsir editorial atas sumber). Bukan ground truth universal; bukan rekaman manusia.",
                   "source_ids": spec.get("source_ids", [])}
            (OUT / "reference" / f"{spec['movement_id']}.json").write_text(json.dumps(ref, separators=(",", ":")), encoding="utf-8")
        brief = {k: v for k, v in checks.items() if k != "arm_keyframes"}
        print(f"klip {spec['movement_id']}: {'OK' if ok else 'PERLU PERBAIKAN'} {brief}", flush=True)

    feats = {m["name"]: m["extras"]["features"] for m in meshes}
    extras = {"silatara": {"character_version": bc.CHARACTER_VERSION, "clips": [c["clip"] for c in clips]}}
    info = bc.write_glb(str(OUT / "silatara-instructor.glb"), J, meshes, anims, extras)
    digest = hashlib.sha256((OUT / "silatara-instructor.glb").read_bytes()).hexdigest()
    fingers = [n for n in names if n[:-2].rstrip("123") in ("Thumb", "Index", "Middle", "Ring", "Pinky")]
    character = {
        "schema": "silatara.character/v1", "character_id": "silatara-instruktur-3d", "version": bc.CHARACTER_VERSION,
        "file": "silatara-instructor.glb", "sha256": digest, "bytes": info["bytes"],
        "format": "glTF 2.0 biner (GLB); skinned mesh, warna verteks, material PBR",
        "joints": names, "joint_count": len(names), "finger_joints": len(fingers),
        "meshes": [{"name": m["name"], "vertices": int(len(m["pos"])), "triangles": int(len(m["idx"])), "features": feats[m["name"]]} for m in meshes],
        "units": "meter", "up_axis": "+Y", "forward_axis": "+Z",
        "license": "Dibuat prosedural oleh SILATARA (tools/character); tanpa model, tekstur, atau animasi pihak ketiga.",
        "costume": "Pakaian latihan generik (baju dan celana gelap, sabuk polos). Tanpa emblem atau warna tingkatan perguruan.",
        "not_a_mascot": True, "source_pipeline": ["tools/character/build_character.py", "tools/character/animate.py", "tools/character/build_all.py"],
        "blender": "Tidak dipakai (tidak tersedia di lingkungan build); pipeline Python ini adalah sumber yang dapat diperbaiki.",
    }
    (OUT / "character.json").write_text(json.dumps(character, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "clips.json").write_text(json.dumps({"schema": "silatara.character-clips/v1", "character_version": bc.CHARACTER_VERSION, "clips": clips}, ensure_ascii=False, indent=1), encoding="utf-8")
    report["summary"] = {"clips": len(clips), "ok": sum(1 for c in report["clips"] if c["ok"]), "glb_bytes": info["bytes"], "build_seconds": round(time.time() - t0, 1)}
    (OUT / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report["summary"]))
    return 0 if report["summary"]["ok"] == len(clips) else 1


if __name__ == "__main__":
    sys.exit(main())
