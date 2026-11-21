"""Klip animasi 3D dari spesifikasi gerak bersumber (content/pencak-silat/animations/*/keyframes.json).

Spesifikasi yang SAMA dengan animasi SVG 2D dipakai ulang (urutan pose, durasi tahan/transisi, interpolasi
smoothstep) sehingga fase dan waktu identik. Setiap pose 2D ditafsirkan ke 3D:
- kaki: IK dua ruas ke posisi pergelangan kaki (kaki tumpu tetap menapak: target tidak bergerak), lutut mengarah
  sesuai putaran telapak;
- lengan: sudut bahu/siku pada bidang pandang (samping = sagital, depan = frontal) + abduksi alami; penghindar
  tabrakan menjauhkan lengan dari badan bila perlu (dicatat di laporan);
- jari: kepalan/terbuka sebagai tekukan tiga ruas;
- torso/kepala/pandangan dari sudut condong.
Keluaran juga mencakup urutan landmark referensi berformat MediaPipe (33 pose + 21 per tangan) untuk penilaian.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from build_character import ANKLE_Y, HIP_Y, Joint, build_rig, hand_frame, unit, v

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/animation"))
import silat_anim as sa  # noqa: E402

FPS = 30
PX = 0.84 / 166.0  # meter per px rig 2D (panjang tungkai 2D 166 px = 0,84 m)
SIDE_ABD = math.radians(9.0)
DEFAULT_SIDE_TURN = 10.0


# ---------------------------------------------------------------- rotasi
def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def axis_angle(axis, ang):
    a = unit(np.asarray(axis, float))
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def frame_from(d, h):
    d = unit(d)
    h = unit(h - d * np.dot(h, d))
    return np.stack([d, h, np.cross(d, h)], 1)


def mat_to_quat(m):
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.array(q)
    return q / np.linalg.norm(q)


# ---------------------------------------------------------------- badan (untuk penghindar tabrakan)
TORSO = [(v(0, 1.275, 0.012), v(0.172, 0.15, 0.118)), (v(0, 1.11, 0.0), v(0.150, 0.15, 0.108)), (v(0, 0.955, -0.005), v(0.168, 0.13, 0.118))]


def torso_sdf(p_local):
    """Jarak bertanda (perkiraan) ke permukaan badan berpakaian; menerima (3,) atau (N,3)."""
    P = np.atleast_2d(p_local)
    d = np.full(len(P), 1e9)
    for c, r in TORSO:
        k0 = np.linalg.norm((P - c) / r, axis=1)
        k1 = np.linalg.norm((P - c) / (r * r), axis=1)
        d = np.minimum(d, k0 * (k0 - 1) / np.maximum(k1, 1e-9))
    return d if np.ndim(p_local) == 2 else float(d[0])


ARM_PTS_U = (0.45, 0.7, 1.0)
ARM_PTS_F = (0.25, 0.5, 0.75, 1.0)
ARM_RADII = np.array([0.05, 0.048, 0.045, 0.042, 0.040, 0.034, 0.030, 0.072, 0.070])  # 2 titik terakhir = kepalan/telapak (± jari tertekuk)


def arm_points(sh, up, fo, Lu, Lf):
    el = sh + up * Lu
    wr = el + fo * Lf
    pts = [sh + up * Lu * t for t in ARM_PTS_U] + [el + fo * Lf * t for t in ARM_PTS_F] + [wr + fo * 0.045, wr + fo * 0.085]
    return np.array(pts)


FIST_RADII = ARM_RADII.copy()
FIST_RADII[-2:] = (0.085, 0.085)  # jari mengepal melengkung ke arah telapak (bisa ke arah badan)


def arm_clearance(sh, up, fo, Lu, Lf, fist=False):
    return float(np.min(torso_sdf(arm_points(sh, up, fo, Lu, Lf)) - (FIST_RADII if fist else ARM_RADII)))


def seg_seg_dist(p1, q1, p2, q2):
    """Jarak minimum dua ruas garis (sampel rapat; cukup untuk validasi)."""
    t = np.linspace(0, 1, 24)
    A = p1 + np.outer(t, q1 - p1)
    B = p2 + np.outer(t, q2 - p2)
    return float(np.min(np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)))


# ---------------------------------------------------------------- solver pose
class Poser:
    def __init__(self, J: dict[str, Joint]):
        self.J = J
        self.names = list(J.keys())
        self.rest = {k: j.pos.copy() for k, j in J.items()}
        self.children = {}
        for j in J.values():
            if j.parent:
                self.children.setdefault(j.parent, []).append(j.name)

    def rest_off(self, b):
        p = self.J[b].parent
        return self.rest[b] - (self.rest[p] if p else 0)

    def fk(self, G: dict, hips_pos):
        """Posisi global semua sendi dari rotasi global G (delta dari istirahat) dan posisi Hips."""
        pos = {"Root": np.zeros(3), "Hips": np.asarray(hips_pos, float)}
        order = [n for n in self.names if n not in ("Root", "Hips")]
        for b in order:
            p = self.J[b].parent
            pos[b] = pos[p] + G[p] @ self.rest_off(b)
        return pos

    def solve(self, view: str, pose: dict, x_ref: float, notes: list, arm_dirs: dict) -> tuple[dict, np.ndarray, dict]:
        G = {n: np.eye(3) for n in self.names}
        px, drop = pose["pelvis"]
        if view == "side":
            hips = v(0, HIP_Y - 0.004 - drop * PX, (px - x_ref) * PX)
        else:
            hips = v((px - x_ref) * PX, HIP_Y - 0.004 - drop * PX, 0)
        tt = math.radians(pose.get("torso", 0))
        lean = rx(tt) if view == "side" else rz(-tt)
        G["Spine"] = rx(tt * 0.5) if view == "side" else rz(-tt * 0.5)
        G["Chest"] = lean
        G["Neck"] = lean
        for s in ("L", "R"):
            G[f"Clavicle.{s}"] = lean
        hd = math.radians(pose.get("head", 0))
        head_r = (rx(tt + hd) if view == "side" else rz(-(tt + hd))) @ ry(math.radians(35 * pose.get("gaze", 0)) if view == "front" else 0)
        G["Head"] = head_r

        pos = self.fk(G, hips)
        # ---- kaki
        for s, sg in (("L", 1.0), ("R", -1.0)):
            fx, lift = pose["feet"][s]
            if view == "side":
                ankle = v(sg * 0.092, ANKLE_Y + lift * PX, (fx - x_ref) * PX)
                turn = DEFAULT_SIDE_TURN
            else:
                ankle = v((fx - x_ref) * PX, ANKLE_Y + lift * PX, 0)
                turn = float(pose["foot_turn"][s])
            yaw = math.radians(turn) * sg
            hip = pos[f"UpperLeg.{s}"]
            pole = ry(yaw * 0.7) @ v(0, 0, 1)
            L1 = np.linalg.norm(self.rest[f"LowerLeg.{s}"] - self.rest[f"UpperLeg.{s}"])
            L2 = np.linalg.norm(self.rest[f"Foot.{s}"] - self.rest[f"LowerLeg.{s}"])
            dvec = ankle - hip
            d = np.linalg.norm(dvec)
            if d > L1 + L2 - 1e-4:
                notes.append({"type": "ik_clamp", "side": s, "excess_m": round(float(d - (L1 + L2)), 4)})
                d = L1 + L2 - 1e-4
                ankle = hip + unit(dvec) * d
            dn = unit(dvec)
            ca = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
            alpha = math.acos(max(-1, min(1, ca)))
            bend_dir = unit(pole - dn * np.dot(pole, dn))
            knee = hip + L1 * (math.cos(alpha) * dn + math.sin(alpha) * bend_dir)
            th_d, sh_d = unit(knee - hip), unit(ankle - knee)
            h = np.cross(th_d, sh_d)
            h = unit(h) if np.linalg.norm(h) > 1e-6 else unit(np.cross(pole, th_d))
            rest_f = frame_from(v(0, -1, 0), v(1, 0, 0))
            G[f"UpperLeg.{s}"] = frame_from(th_d, h) @ rest_f.T
            G[f"LowerLeg.{s}"] = frame_from(sh_d, h) @ rest_f.T
            G[f"Foot.{s}"] = ry(yaw)
            G[f"Toes.{s}"] = ry(yaw)
        # ---- lengan: arah (kerangka dada) dari penyelesaian keyframe + koreksi kecil per frame bila perlu
        for s, sg in (("L", 1.0), ("R", -1.0)):
            up, fo, twist = arm_dirs[s]
            up, fo, fix = self._frame_clear(s, sg, up, fo, view)
            if fix:
                notes.append({"type": "arm_clearance", "side": s, **fix})
            up_w, fo_w = lean @ up, lean @ fo
            rest_dir = unit(self.rest[f"LowerArm.{s}"] - self.rest[f"UpperArm.{s}"])
            rest_h = unit(np.cross(rest_dir, v(0, 0, 1)) * sg)  # sumbu engsel siku saat istirahat
            h = np.cross(up_w, fo_w)
            if np.linalg.norm(h) < 1e-4:
                h = G["Chest"] @ rest_h
            else:
                h = unit(h)
                if np.dot(h, G["Chest"] @ rest_h) < 0:
                    h = -h
            rf = frame_from(rest_dir, rest_h)
            G[f"UpperArm.{s}"] = frame_from(up_w, h) @ rf.T
            fore = frame_from(fo_w, h) @ rf.T
            # rotasi lengan bawah (pronasi/supinasi) dibagi dua: setengah di lengan bawah, sisanya di pergelangan
            G[f"LowerArm.{s}"] = axis_angle(fo_w, math.radians(twist * 0.5)) @ fore
            G[f"Hand.{s}"] = axis_angle(fo_w, math.radians(twist)) @ fore
        # ---- jari (rotasi lokal terhadap tangan)
        local_extra = {}
        for s in ("L", "R"):
            state = pose["hands"][s]
            u, t, n = hand_frame(s)
            for f in ("Index", "Middle", "Ring", "Pinky"):
                curls = FIST[f] if state == "fist" else OPEN[f]
                for i in range(3):
                    b = f"{f}{i + 1}.{s}"
                    d = unit(self.J[b].tail - self.J[b].pos)
                    local_extra[b] = axis_angle(np.cross(d, n), math.radians(curls[i]))
            # ibu jari: arah tiap ruas ditentukan eksplisit pada kerangka tangan (u jari, t sisi ibu jari, n telapak)
            d0 = unit(self.J[f"Thumb1.{s}"].tail - self.J[f"Thumb1.{s}"].pos)
            targets = THUMB_FIST if state == "fist" else THUMB_OPEN
            acc = np.eye(3)
            for i in range(3):
                tgt = unit(targets[i][0] * u + targets[i][1] * t + targets[i][2] * n)
                R_i = align(d0, tgt)
                local_extra[f"Thumb{i + 1}.{s}"] = acc.T @ R_i
                acc = R_i
        for s in ("L", "R"):
            for f in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
                par = f"Hand.{s}"
                for i in range(3):
                    b = f"{f}{i + 1}.{s}"
                    G[b] = G[par] @ local_extra[b]
                    par = b
        pos = self.fk(G, hips)
        targets = {"ankles": {s: ankle_target(view, pose, s, x_ref) for s in ("L", "R")}}
        return G, hips, {"pos": pos, "targets": targets}

    def lens(self, s):
        sh = self.rest[f"UpperArm.{s}"]
        return sh, np.linalg.norm(self.rest[f"LowerArm.{s}"] - sh), np.linalg.norm(self.rest[f"Hand.{s}"] - self.rest[f"LowerArm.{s}"])

    def keyframe_arms(self, view: str, pose: dict, text: str, waist_sig: set | None = None) -> tuple[dict, list]:
        """Arah lengan 3D (kerangka dada) untuk satu keyframe. Gambar 2D hanya memuat sudut pada bidang pandang;
        dimensi yang hilang (kedalaman pada tampak depan, ke samping pada tampak samping) diisi dengan koreksi TERKECIL
        yang membuat lengan & kepalan bebas dari badan dan lengan kiri-kanan tidak saling tembus."""
        notes = []
        t = text.lower()
        sig = json.dumps([pose["arms"], pose["hands"]], sort_keys=True)
        waist = ("pinggang" in t and all(pose["hands"][x] == "fist" for x in ("L", "R"))) or (waist_sig is not None and sig in waist_sig)
        crossed = "silang" in t or "bersilang" in t or "memegang pergelangan" in t
        cands = {}
        for s, sg in (("L", 1.0), ("R", -1.0)):
            sh, Lu, Lf = self.lens(s)
            if waist:
                # 'kepalan di pinggang' (sikap tegak 2): konfigurasi rig tampak samping (bahu -28°, siku 95°)
                a_sh, a_el = math.radians(-28), math.radians(95)
                base_u = v(0, -math.cos(a_sh), math.sin(a_sh))
                base_f = v(0, -math.cos(a_sh + a_el), math.sin(a_sh + a_el))
            elif view == "side":
                a_sh, a_el = (math.radians(x) for x in pose["arms"][s])
                base_u = v(0, -math.cos(a_sh), math.sin(a_sh))
                base_f = v(0, -math.cos(a_sh + a_el), math.sin(a_sh + a_el))
            else:
                a_sh, a_el = (math.radians(x) for x in pose["arms"][s])
                base_u = v(sg * math.sin(a_sh), -math.cos(a_sh), 0.0)
                base_f = v(sg * math.sin(a_sh - a_el), -math.cos(a_sh - a_el), 0.0)
            depth_ok = view == "front" and not waist
            lst = []
            for ab in range(0, 31, 3):
                Rab = rz(sg * math.radians(ab + (9 if not depth_ok else 0)))
                for bu in (np.linspace(-0.6, 0.6, 13) if depth_ok else (0.0,)):
                    for bf in (np.linspace(0, 2.4, 25) if depth_ok else (0.0,)):
                        u2 = Rab @ unit(base_u + v(0, 0, bu))
                        f2 = Rab @ unit(base_f + v(0, 0, bf))
                        if arm_clearance(sh, u2, f2, Lu, Lf, pose["hands"][s] == "fist" and not waist) >= -0.004:
                            lst.append((ab / 30 + abs(bu) + 0.5 * bf, u2, f2, {"abduksi_tambahan_deg": ab, "depth_upper": round(float(bu), 2), "depth_fore": round(float(bf), 2)}))
            lst.sort(key=lambda x: x[0])
            cands[s] = lst[:400]

        def gap(a, b):
            sL, LuL, LfL = self.lens("L")
            sR, LuR, LfR = self.lens("R")
            eL, eR = sL + a[1] * LuL, sR + b[1] * LuR
            return seg_seg_dist(eL, eL + a[2] * (LfL + 0.09), eR, eR + b[2] * (LfR + 0.09))

        best = None
        for a in cands["L"][:60]:
            for b in cands["R"]:
                if a[0] + b[0] >= (best[0] if best else 1e9):
                    break
                if gap(a, b) >= 0.075:
                    best = (a[0] + b[0], a, b)
                    break
        out = {}
        twist = {s: (-sg * 90.0 if waist else 0.0) for s, sg in (("L", 1.0), ("R", -1.0))}  # pinggang: telapak menghadap atas
        if best is None:
            notes.append({"type": "arm_keyframe_unresolved", "side": "LR", "crossed": crossed})
            for s in ("L", "R"):
                c = cands[s][0] if cands[s] else (0, v(0, -1, 0), v(0, -1, 0), {})
                out[s] = (c[1], c[2], twist[s])
        else:
            for s, c in (("L", best[1]), ("R", best[2])):
                out[s] = (c[1], c[2], twist[s])
                notes.append({"type": "arm_keyframe", "side": s, "mode": "pinggang" if waist else view, **c[3]})
        return out, notes

    def _frame_clear(self, s, sg, up, fo, view):
        """Selama transisi, arah hasil interpolasi bisa menyentuh badan: dorong sedikit (ke depan/samping) bila perlu."""
        sh, Lu, Lf = self.lens(s)
        if arm_clearance(sh, up, fo, Lu, Lf) >= -0.004:
            return up, fo, None
        for k in range(1, 31):
            a = math.radians(1.5 * k)
            for kind, R in (("fleksi", rx(-a)), ("abduksi", rz(sg * a)), ("ekstensi", rx(a))):
                u2, f2 = R @ up, R @ fo
                if arm_clearance(sh, u2, f2, Lu, Lf) >= -0.004:
                    return u2, f2, {"correction": kind, "degrees": 1.5 * k}
        return up, fo, {"correction": "tidak_terselesaikan", "degrees": 45.0}


def align(a, b):
    """Rotasi terpendek yang memetakan vektor satuan a ke b."""
    a, b = unit(a), unit(b)
    c = float(np.dot(a, b))
    if c > 1 - 1e-9:
        return np.eye(3)
    ax = np.cross(a, b)
    if np.linalg.norm(ax) < 1e-9:
        ax = np.cross(a, v(1, 0, 0)) if abs(a[0]) < 0.9 else np.cross(a, v(0, 1, 0))
    return axis_angle(ax, math.acos(max(-1.0, min(1.0, c))))


# arah ruas ibu jari pada kerangka tangan (u, t, n): mengepal = melintang di depan jari, sisi telapak
THUMB_FIST = ((0.70, 0.30, 0.65), (0.45, -0.30, 0.85), (0.10, -0.75, 0.65))
THUMB_OPEN = ((0.62, 0.70, 0.30), (0.66, 0.66, 0.28), (0.70, 0.62, 0.25))
FIST = {"Thumb": (0, 0, 0), "Index": (88, 102, 66), "Middle": (90, 104, 66), "Ring": (92, 104, 64), "Pinky": (94, 102, 62)}
OPEN = {"Thumb": (6, 8, 6), "Index": (8, 10, 6), "Middle": (9, 11, 6), "Ring": (10, 12, 7), "Pinky": (12, 13, 8)}


def ankle_target(view, pose, s, x_ref):
    fx, lift = pose["feet"][s]
    sg = 1.0 if s == "L" else -1.0
    if view == "side":
        return v(sg * 0.092, ANKLE_Y + lift * PX, (fx - x_ref) * PX)
    return v((fx - x_ref) * PX, ANKLE_Y + lift * PX, 0)


# ---------------------------------------------------------------- landmark referensi (indeks MediaPipe)
def landmarks(pos: dict, G: dict) -> tuple[list, dict]:
    hp = pos["Head"]
    H = G["Head"]
    rest_head = v(0, 1.52, 0.008)

    def head_pt(p):
        return hp + H @ (p - rest_head)
    lm = [None] * 33
    lm[0] = head_pt(v(0, 1.556, 0.112))
    for i, (x, y) in {1: (0.019, 1.596), 2: (0.031, 1.594), 3: (0.043, 1.594), 4: (-0.019, 1.596), 5: (-0.031, 1.594), 6: (-0.043, 1.594)}.items():
        lm[i] = head_pt(v(x, y, 0.082))
    lm[7], lm[8] = head_pt(v(0.082, 1.582, 0.004)), head_pt(v(-0.082, 1.582, 0.004))
    lm[9], lm[10] = head_pt(v(0.016, 1.523, 0.1)), head_pt(v(-0.016, 1.523, 0.1))
    for s, o in (("L", 0), ("R", 1)):
        lm[11 + o] = pos[f"UpperArm.{s}"]
        lm[13 + o] = pos[f"LowerArm.{s}"]
        lm[15 + o] = pos[f"Hand.{s}"]
        lm[17 + o] = pos[f"Pinky1.{s}"]
        lm[19 + o] = pos[f"Index1.{s}"]
        lm[21 + o] = pos[f"Thumb2.{s}"]
        lm[23 + o] = pos[f"UpperLeg.{s}"]
        lm[25 + o] = pos[f"LowerLeg.{s}"]
        lm[27 + o] = pos[f"Foot.{s}"]
        lm[29 + o] = pos[f"Foot.{s}"] + G[f"Foot.{s}"] @ v(0, -0.07, -0.06)
        lm[31 + o] = pos[f"Toes.{s}"] + G[f"Toes.{s}"] @ v(0, -0.01, 0.05)
    hands = {}
    for s in ("L", "R"):
        pts = [pos[f"Hand.{s}"]]
        for f in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
            for i in range(3):
                pts.append(pos[f"{f}{i + 1}.{s}"])
            # ujung jari = ujung ruas ke-3 setelah rotasi
            b = f"{f}3.{s}"
            pts.append(pos[b] + G[b] @ (J_TAIL[b] - J_POS[b]))
        hands[s] = pts
    return lm, hands


J_TAIL: dict = {}
J_POS: dict = {}


def build_clip(poser: Poser, spec: dict) -> dict:
    segs, total = sa.expand_timeline(spec)
    view = spec["view"]
    first = sa.full_pose(spec["keyframes"][0]["pose"])
    x_ref = first["pelvis"][0]
    n = max(2, round(total / 1000 * FPS))
    frames, notes = [], []
    kf_arms = {}
    waist_sig = set()
    for k in spec["keyframes"]:
        fp = sa.full_pose(k["pose"])
        if "pinggang" in f"{k.get('label', '')} {k.get('caption', '')}".lower() and all(fp["hands"][x] == "fist" for x in ("L", "R")):
            waist_sig.add(json.dumps([fp["arms"], fp["hands"]], sort_keys=True))
    for k in spec["keyframes"]:
        arms, kn = poser.keyframe_arms(view, sa.full_pose(k["pose"]), f"{k.get('label', '')} {k.get('caption', '')}", waist_sig)
        kf_arms[k["id"]] = arms
        notes += [{**x, "keyframe": k["id"]} for x in kn]
    for i in range(n + 1):
        t = total * i / n
        pose, kf_id = sa.pose_at(segs, t)
        arm_dirs = arms_at(segs, t, kf_arms)
        fr_notes: list = []
        G, hips, info = poser.solve(view, pose, x_ref, fr_notes, arm_dirs)
        for nt in fr_notes:
            nt["t"] = round(t / 1000, 3)
        notes += fr_notes
        frames.append({"t": t / 1000.0, "G": G, "hips": hips, "pos": info["pos"], "targets": info["targets"], "kf": kf_id, "pose": pose})
    windows = sa.phase_windows(segs, total)
    kfs = {k["id"]: k for k in spec["keyframes"]}
    phases = []
    for kid, w in windows.items():
        k = kfs[kid]
        for a, b in zip(w[0::2], w[1::2], strict=True):
            phases.append({"phase_id": k.get("phase_id"), "keyframe": kid, "label": k.get("label"), "caption": k.get("caption"),
                           "start": round(a * total / 1000, 3), "end": round(b * total / 1000, 3)})
    phases.sort(key=lambda p: p["start"])
    return {"frames": frames, "duration": total / 1000.0, "phases": phases, "notes": notes, "view": view}


def arms_at(segs, t, kf_arms):
    """Interpolasi arah lengan 3D dengan waktu & smoothstep yang sama seperti pose_at."""
    for a, b, k0, k1, kind in segs:
        if t <= b + 1e-9:
            if kind == "hold":
                return kf_arms[k0["id"]]
            u = sa.smoothstep(0.0 if b == a else (t - a) / (b - a))
            A, B = kf_arms[k0["id"]], kf_arms[k1["id"]]
            return {s: (unit(A[s][0] * (1 - u) + B[s][0] * u), unit(A[s][1] * (1 - u) + B[s][1] * u), A[s][2] * (1 - u) + B[s][2] * u)
                    for s in ("L", "R")}
    last = segs[-1][3]["id"]
    return kf_arms[last]


def tracks_from_frames(poser: Poser, frames: list, tol=0.0006) -> list[dict]:
    times = np.array([f["t"] for f in frames])
    out = []
    for b in poser.names:
        if b == "Root":
            continue
        p = poser.J[b].parent
        qs = []
        for f in frames:
            Gp = f["G"][p] if p else np.eye(3)
            q = mat_to_quat(Gp.T @ f["G"][b])
            if qs and np.dot(q, qs[-1]) < 0:
                q = -q
            qs.append(q)
        qs = np.array(qs)
        keep = reduce_keys(times, qs, tol)
        out.append({"joint": b, "path": "rotation", "times": times[keep], "values": qs[keep]})
    hp = np.array([f["hips"] for f in frames])
    keep = reduce_keys(times, hp, 0.0003)
    out.append({"joint": "Hips", "path": "translation", "times": times[keep], "values": hp[keep]})
    return out


def reduce_keys(times, vals, tol):
    """Buang key yang dapat direkonstruksi interpolasi linier (galat < tol); key pertama/terakhir dipertahankan."""
    keep = [0]
    for i in range(1, len(times) - 1):
        a = keep[-1]
        b = i + 1
        ok = True
        for j in range(a + 1, b):
            u = (times[j] - times[a]) / (times[b] - times[a])
            if np.max(np.abs(vals[a] + (vals[b] - vals[a]) * u - vals[j])) > tol:
                ok = False
                break
        if not ok:
            keep.append(i)
    keep.append(len(times) - 1)
    return np.array(keep)


__all__ = ["Poser", "build_clip", "tracks_from_frames", "landmarks", "build_rig", "J_TAIL", "J_POS"]
