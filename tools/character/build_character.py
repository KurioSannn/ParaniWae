"""Generator karakter instruksional 3D SILATARA (prosedural, dapat direproduksi, tanpa aset pihak ketiga).

Pipeline: primitif SDF (permukaan implisit) -> marching cubes (scikit-image) -> normal dari gradien SDF ->
warna verteks per wilayah -> bobot skin berbasis jarak ke ruas tulang (dibatasi wilayah tubuh) -> glTF 2.0 biner (GLB)
dengan rig 52 sendi (termasuk 3 ruas per jari) dan banyak klip animasi (lihat animate.py).

Bukan maskot SILATARA. Pakaian latihan generik tanpa emblem atau warna tingkatan perguruan mana pun.
Satuan meter, sumbu Y ke atas, karakter menghadap +Z (konvensi glTF). Sisi KIRI karakter = +X.
"""
from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field

import numpy as np
from skimage.measure import marching_cubes

CHARACTER_VERSION = "1.0.0"

# ---------------------------------------------------------------- rig (pose istirahat: A-pose 30°)
SH_ABD = np.radians(30.0)
ARM_DIR = {s: np.array([sg * np.sin(SH_ABD), -np.cos(SH_ABD), 0.0]) for s, sg in (("L", 1.0), ("R", -1.0))}
UPPER_ARM, FOREARM = 0.28, 0.25
THIGH, SHIN = 0.42, 0.42
HIP_Y, HIP_JOINT_Y, ANKLE_Y = 0.95, 0.92, 0.08
HIP_X = 0.092


def v(*a) -> np.ndarray:
    return np.array(a, dtype=float)


def unit(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a)
    return a / n if n > 1e-12 else a


@dataclass
class Joint:
    name: str
    parent: str | None
    pos: np.ndarray  # posisi global saat istirahat
    tail: np.ndarray  # ujung ruas (untuk bobot skin)


def hand_frame(side: str):
    """(u: arah jari, t: sisi ibu jari, n: normal telapak) pada pose istirahat."""
    u = ARM_DIR[side]
    fwd = v(0, 0, 1)
    t = unit(fwd - u * np.dot(fwd, u))
    n = np.cross(u, t) if side == "L" else np.cross(t, u)
    return u, t, unit(n)


FINGERS = {
    # nama: (offset t pangkal, sudut sebar (°, ke arah t), panjang ruas, jari-jari pangkal, jari-jari ujung)
    "Index": (0.026, 6.0, (0.046, 0.028, 0.023), 0.0090, 0.0070),
    "Middle": (0.008, 0.0, (0.051, 0.032, 0.024), 0.0092, 0.0072),
    "Ring": (-0.010, -5.0, (0.048, 0.030, 0.023), 0.0086, 0.0067),
    "Pinky": (-0.026, -12.0, (0.037, 0.023, 0.020), 0.0078, 0.0060),
}
THUMB = ((0.040, 0.034, 0.028), 0.0110, 0.0080)


def finger_chain(side: str, name: str, wrist: np.ndarray):
    u, t, n = hand_frame(side)
    if name == "Thumb":
        lens, r0, r1 = THUMB
        base = wrist + u * 0.022 + t * 0.022 + n * 0.010
        d = unit(0.62 * u + 0.70 * t + 0.30 * n)
    else:
        off, spread, lens, r0, r1 = FINGERS[name]
        base = wrist + u * 0.092 + t * off
        a = np.radians(spread)
        d = unit(np.cos(a) * u + np.sin(a) * t)
    pts = [base]
    for L in lens:
        pts.append(pts[-1] + d * L)
    return pts, d, (r0, r1)


def build_rig() -> dict[str, Joint]:
    J: dict[str, Joint] = {}

    def add(name, parent, pos, tail):
        J[name] = Joint(name, parent, np.asarray(pos, float), np.asarray(tail, float))

    add("Root", None, v(0, 0, 0), v(0, 0.1, 0))
    add("Hips", "Root", v(0, HIP_Y, 0), v(0, 1.05, 0))
    add("Spine", "Hips", v(0, 1.05, 0), v(0, 1.25, 0.005))
    add("Chest", "Spine", v(0, 1.25, 0.005), v(0, 1.43, 0.0))
    add("Neck", "Chest", v(0, 1.43, 0.0), v(0, 1.52, 0.008))
    add("Head", "Neck", v(0, 1.52, 0.008), v(0, 1.69, 0.008))
    for s, sg in (("L", 1.0), ("R", -1.0)):
        sh = v(sg * 0.175, 1.385, 0.0)
        el = sh + ARM_DIR[s] * UPPER_ARM
        wr = el + ARM_DIR[s] * FOREARM
        add(f"Clavicle.{s}", "Chest", v(sg * 0.03, 1.39, 0.01), sh)
        add(f"UpperArm.{s}", f"Clavicle.{s}", sh, el)
        add(f"LowerArm.{s}", f"UpperArm.{s}", el, wr)
        add(f"Hand.{s}", f"LowerArm.{s}", wr, wr + ARM_DIR[s] * 0.09)
        for fname in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
            pts, _, _ = finger_chain(s, fname, wr)
            parent = f"Hand.{s}"
            for i in range(3):
                nm = f"{fname}{i + 1}.{s}"
                add(nm, parent, pts[i], pts[i + 1])
                parent = nm
        hip = v(sg * HIP_X, HIP_JOINT_Y, 0.0)
        knee = v(sg * HIP_X, HIP_JOINT_Y - THIGH, 0.0)
        ankle = v(sg * HIP_X, ANKLE_Y, 0.0)
        ball = ankle + v(0, -0.06, 0.135)
        add(f"UpperLeg.{s}", "Hips", hip, knee)
        add(f"LowerLeg.{s}", f"UpperLeg.{s}", knee, ankle)
        add(f"Foot.{s}", f"LowerLeg.{s}", ankle, ball)
        add(f"Toes.{s}", f"Foot.{s}", ball, ball + v(0, 0, 0.06))
    return J


# ---------------------------------------------------------------- SDF
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def sd_ellipsoid(p, c, r, R=None):
    q = p - c
    if R is not None:
        q = q @ R  # ke kerangka lokal (kolom R = sumbu lokal)
    r = np.asarray(r, float)
    k0 = np.linalg.norm(q / r, axis=-1)
    k1 = np.linalg.norm(q / (r * r), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sd_round_cone(p, a, b, r1, r2):
    """Kapsul dengan dua jari-jari (IQ sdRoundCone), tervektorisasi."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ba = b - a
    l2 = float(ba @ ba)
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    xv = pa * l2 - np.outer(y, ba)
    x2 = np.einsum("ij,ij->i", xv, xv)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d_end = np.sqrt(x2 + z2) * il2 - r2
    d_start = np.sqrt(x2 + y2) * il2 - r1
    d_mid = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1
    return np.where(np.sign(z) * a2 * z2 > k, d_end, np.where(np.sign(y) * a2 * y2 < k, d_start, d_mid))


def sd_capsule(p, a, b, r):
    return sd_round_cone(p, a, b, r, r)


def sd_plane(p, point, normal):
    """>0 di sisi normal."""
    return (p - point) @ unit(np.asarray(normal, float))


@dataclass
class Prim:
    fn: object  # callable(p) -> d
    bone: str
    k: float = 0.02  # kehalusan sambungan ke gabungan sebelumnya
    op: str = "union"  # union | subtract | intersect
    tag: str = ""


@dataclass
class Part:
    name: str
    prims: list[Prim]
    bounds: tuple[np.ndarray, np.ndarray]
    step: float
    color: tuple[int, int, int]
    material: str
    allowed: set[str] | None = None  # bone yang boleh dipakai untuk bobot
    tint: list = field(default_factory=list)  # [(fn, color, width)]

    def sdf(self, p, per_prim: bool = False):
        d = None
        dists = []
        for pr in self.prims:
            di = pr.fn(p)
            if pr.op == "union":
                dists.append(di)
            d = di if d is None else (smin(d, di, pr.k) if pr.op == "union" else
                                       smax(d, -di, pr.k) if pr.op == "subtract" else smax(d, di, pr.k))
        return (d, dists) if per_prim else d


# ---------------------------------------------------------------- bagian tubuh
SKIN = (176, 128, 92)      # sawo matang
LIP = (150, 88, 76)
HAIR = (28, 22, 19)
CLOTH = (30, 59, 50)        # #1E3B32 (token forest-900)
SASH = (185, 133, 79)       # #B9854F (token bronze-500), polos tanpa tanda tingkatan
EYE_WHITE = (238, 234, 226)
IRIS = (74, 47, 31)
PUPIL = (12, 9, 8)
NAIL = (196, 150, 120)


def rot_cols(x, y, z):
    return np.stack([unit(x), unit(y), unit(z)], axis=1)


def build_parts(J: dict[str, Joint]) -> list[Part]:
    P = []
    jp = {k: j.pos for k, j in J.items()}
    # ---------------- pakaian (baju + celana): permukaan tubuh yang tertutup kain
    cloth = [
        Prim(lambda p: sd_ellipsoid(p, v(0, 0.955, -0.005), (0.168, 0.13, 0.118)), "Hips", tag="pelvis"),
        Prim(lambda p: sd_ellipsoid(p, v(0, 1.11, 0.0), (0.150, 0.15, 0.108)), "Spine", 0.06, tag="abdomen"),
        Prim(lambda p: sd_ellipsoid(p, v(0, 1.275, 0.012), (0.172, 0.15, 0.118)), "Chest", 0.06, tag="chest"),
        Prim(lambda p: sd_capsule(p, v(0.15, 1.375, 0), v(-0.15, 1.375, 0), 0.066), "Chest", 0.05, tag="shoulders"),
    ]
    for s, sg in (("L", 1.0), ("R", -1.0)):
        sh, el, wr = jp[f"UpperArm.{s}"], jp[f"LowerArm.{s}"], jp[f"Hand.{s}"]
        sleeve_end = el + (wr - el) * 0.86
        cloth += [
            Prim(lambda p, sh=sh, s=s: sd_ellipsoid(p, sh + v(0, -0.01, 0) + ARM_DIR[s] * 0.02, (0.072, 0.07, 0.07)), f"Clavicle.{s}", 0.04, tag="deltoid"),
            Prim(lambda p, sh=sh, el=el: sd_round_cone(p, sh, el, 0.058, 0.046), f"UpperArm.{s}", 0.03),
            # lengan baju dipotong rata di ujung (potongan lokal pada ruas ini saja)
            Prim(lambda p, el=el, se=sleeve_end, d=unit(wr - el): np.maximum(sd_round_cone(p, el, se + d * 0.03, 0.046, 0.040), (p - se) @ d),
                 f"LowerArm.{s}", 0.02),
        ]
        hip, knee, ank = jp[f"UpperLeg.{s}"], jp[f"LowerLeg.{s}"], jp[f"Foot.{s}"]
        hem = ank + v(0, 0.05, 0)
        cloth += [
            Prim(lambda p, hip=hip, knee=knee: sd_round_cone(p, hip + v(0, 0.02, 0), knee, 0.092, 0.068), f"UpperLeg.{s}", 0.05),
            Prim(lambda p, knee=knee, hem=hem: np.maximum(sd_round_cone(p, knee, hem - v(0, 0.03, 0), 0.068, 0.062), hem[1] - p[:, 1]),
                 f"LowerLeg.{s}", 0.02),
        ]
    # leher baju (bukaan kerah) dan potongan ujung lengan/celana (rata)
    cloth.append(Prim(lambda p: sd_capsule(p, v(0, 1.395, 0.012), v(0, 1.7, 0.02), 0.06), "Chest", 0.012, op="subtract"))
    P.append(Part("outfit", cloth, (v(-0.52, 0.10, -0.19), v(0.52, 1.47, 0.19)), 0.0115, CLOTH, "cloth"))

    # ---------------- sabuk polos
    def sash(p):
        q = p - v(0, 1.005, 0.004)
        ell = np.sqrt((q[:, 0] / 0.170) ** 2 + (q[:, 2] / 0.124) ** 2) - 1.0
        band = np.maximum(ell * 0.13, np.abs(q[:, 1]) - 0.026)
        return band
    # simpul di sisi kiri pinggul; ujung sabuk pendek, pipih, menggantung di samping (bukan di tengah depan)
    knot = lambda p: sd_ellipsoid(p, v(0.158, 1.0, 0.055), (0.018, 0.022, 0.026))  # noqa: E731
    tail1 = lambda p: sd_ellipsoid(p, v(0.172, 0.95, 0.05), (0.008, 0.05, 0.022))  # noqa: E731
    tail2 = lambda p: sd_ellipsoid(p, v(0.17, 0.955, 0.078), (0.008, 0.042, 0.018))  # noqa: E731
    P.append(Part("sash", [Prim(sash, "Hips"), Prim(knot, "Hips", 0.01), Prim(tail1, "Hips", 0.008), Prim(tail2, "Hips", 0.008)],
                  (v(-0.2, 0.83, -0.15), v(0.2, 1.05, 0.16)), 0.0055, SASH, "cloth"))

    # ---------------- kulit: leher, pergelangan, kaki (telapak rata di lantai)
    skin = [Prim(lambda p: sd_round_cone(p, v(0, 1.37, 0.0), v(0, 1.52, 0.014), 0.056, 0.05), "Neck", tag="neck")]
    for s, sg in (("L", 1.0), ("R", -1.0)):
        el, wr = jp[f"LowerArm.{s}"], jp[f"Hand.{s}"]
        skin.append(Prim(lambda p, a=el + (wr - el) * 0.72, b=wr + ARM_DIR[s] * 0.012: sd_round_cone(p, a, b, 0.031, 0.026), f"LowerArm.{s}", 0.01))
        ank, ball = jp[f"Foot.{s}"], jp[f"Toes.{s}"]
        skin += [
            Prim(lambda p, a=ank: sd_round_cone(p, a + v(0, 0.13, 0), a, 0.041, 0.037), f"LowerLeg.{s}", 0.01),
            Prim(lambda p, a=ank: sd_ellipsoid(p, a + v(0, -0.045, -0.028), (0.034, 0.038, 0.042)), f"Foot.{s}", 0.03, tag="heel"),
            Prim(lambda p, a=ank: sd_ellipsoid(p, a + v(0, -0.05, 0.06), (0.043, 0.032, 0.095)), f"Foot.{s}", 0.03, tag="foot"),
        ]
        # jari kaki: jempol lebih besar, ruas pendek
        for i, (dx, r, ln) in enumerate(((0.024, 0.013, 0.045), (0.006, 0.010, 0.040), (-0.007, 0.0095, 0.036), (-0.018, 0.009, 0.032), (-0.028, 0.0085, 0.027))):
            st = ball + v(sg * dx, -0.008, -0.01)
            skin.append(Prim(lambda p, st=st, ln=ln, r=r: sd_round_cone(p, st, st + v(0, -0.004, ln), r, r * 0.85), f"Toes.{s}", 0.008, tag=f"toe{i}"))
        skin.append(Prim(lambda p: -p[:, 1], f"Foot.{s}", 0.003, op="intersect"))  # telapak rata pada y=0
    P.append(Part("skin_body", skin, (v(-0.5, -0.01, -0.12), v(0.5, 1.56, 0.30)), 0.0058, SKIN, "skin"))

    # ---------------- kepala (resolusi tinggi)
    hc = v(0, 1.588, 0.008)
    head = [
        Prim(lambda p: sd_ellipsoid(p, hc, (0.077, 0.098, 0.094)), "Head", tag="cranium"),
        Prim(lambda p: sd_ellipsoid(p, v(0, 1.535, 0.036), (0.060, 0.056, 0.068)), "Head", 0.03, tag="jaw"),
        Prim(lambda p: sd_ellipsoid(p, v(0, 1.497, 0.072), (0.022, 0.018, 0.020)), "Head", 0.02, tag="chin"),
        Prim(lambda p: sd_ellipsoid(p, v(0.044, 1.566, 0.066), (0.024, 0.018, 0.022)), "Head", 0.02, tag="cheek"),
        Prim(lambda p: sd_ellipsoid(p, v(-0.044, 1.566, 0.066), (0.024, 0.018, 0.022)), "Head", 0.02, tag="cheek"),
        Prim(lambda p: sd_ellipsoid(p, v(0, 1.618, 0.078), (0.058, 0.014, 0.018)), "Head", 0.02, tag="brow_ridge"),
        # hidung: batang + ujung + cuping
        Prim(lambda p: sd_round_cone(p, v(0, 1.598, 0.090), v(0, 1.556, 0.112), 0.0085, 0.0125), "Head", 0.012, tag="nose"),
        Prim(lambda p: sd_ellipsoid(p, v(0.0115, 1.551, 0.101), (0.0095, 0.0075, 0.0085)), "Head", 0.008, tag="nose"),
        Prim(lambda p: sd_ellipsoid(p, v(-0.0115, 1.551, 0.101), (0.0095, 0.0075, 0.0085)), "Head", 0.008, tag="nose"),
        # bibir atas & bawah
        Prim(lambda p: sd_ellipsoid(p, v(0, 1.5285, 0.0965), (0.0215, 0.0062, 0.0095)), "Head", 0.006, tag="lip"),
        Prim(lambda p: sd_ellipsoid(p, v(0, 1.5175, 0.0950), (0.0185, 0.0072, 0.0092)), "Head", 0.006, tag="lip"),
        # telinga + cekungan daun telinga
        Prim(lambda p: sd_ellipsoid(p, v(0.079, 1.582, 0.004), (0.011, 0.030, 0.019), rot_cols(v(1, 0, 0.25), v(0, 1, -0.12), v(-0.25, 0.1, 1))), "Head", 0.008, tag="ear"),
        Prim(lambda p: sd_ellipsoid(p, v(-0.079, 1.582, 0.004), (0.011, 0.030, 0.019), rot_cols(v(1, 0, -0.25), v(0, 1, -0.12), v(0.25, 0.1, 1))), "Head", 0.008, tag="ear"),
        Prim(lambda p: sd_ellipsoid(p, v(0.091, 1.582, 0.010), (0.004, 0.015, 0.0085)), "Head", 0.003, op="subtract"),
        Prim(lambda p: sd_ellipsoid(p, v(-0.091, 1.582, 0.010), (0.004, 0.015, 0.0085)), "Head", 0.003, op="subtract"),
        # rongga mata & garis mulut
        Prim(lambda p: sd_ellipsoid(p, v(0.031, 1.594, 0.077), (0.0175, 0.0125, 0.012)), "Head", 0.008, op="subtract"),
        Prim(lambda p: sd_ellipsoid(p, v(-0.031, 1.594, 0.077), (0.0175, 0.0125, 0.012)), "Head", 0.008, op="subtract"),
        Prim(lambda p: sd_capsule(p, v(-0.019, 1.5232, 0.1035), v(0.019, 1.5232, 0.1035), 0.0016), "Head", 0.002, op="subtract"),
        # kelopak mata (SETELAH rongga mata dipahat, agar tidak ikut terpotong)
        Prim(lambda p: sd_ellipsoid(p, v(0.031, 1.5992, 0.0795), (0.0158, 0.0058, 0.0098)), "Head", 0.004, tag="eyelid"),
        Prim(lambda p: sd_ellipsoid(p, v(-0.031, 1.5992, 0.0795), (0.0158, 0.0058, 0.0098)), "Head", 0.004, tag="eyelid"),
        Prim(lambda p: sd_ellipsoid(p, v(0.031, 1.5872, 0.0790), (0.0148, 0.0042, 0.0090)), "Head", 0.004, tag="eyelid"),
        Prim(lambda p: sd_ellipsoid(p, v(-0.031, 1.5872, 0.0790), (0.0148, 0.0042, 0.0090)), "Head", 0.004, tag="eyelid"),
    ]
    lips = [pr.fn for pr in head if pr.tag == "lip"]
    P.append(Part("head", head, (v(-0.11, 1.46, -0.105), v(0.11, 1.70, 0.135)), 0.0027, SKIN, "skin",
                  tint=[(lambda p: np.minimum(lips[0](p), lips[1](p)), LIP, 0.0025)]))

    # ---------------- rambut pendek + alis
    def hair_cap(p):
        d = sd_ellipsoid(p, hc + v(0, 0.006, -0.006), (0.0835, 0.1045, 0.1005))
        keep = sd_plane(p, v(0, 1.632, 0.08), v(0, 1.0, -0.95))  # >0 = di atas garis rambut (dahi tinggi, tengkuk rendah)
        return smax(d, -keep, 0.008)
    hair = [Prim(hair_cap, "Head", tag="hair")]
    P.append(Part("hair", hair, (v(-0.10, 1.46, -0.12), v(0.10, 1.71, 0.12)), 0.0028, HAIR, "hair"))
    brows = []
    for sg in (1.0, -1.0):
        brows.append(Prim(lambda p, sg=sg: sd_round_cone(p, v(sg * 0.014, 1.6125, 0.1010), v(sg * 0.050, 1.6118, 0.0905), 0.0046, 0.0030), "Head", 0.002, tag="brow"))
    P.append(Part("brows", brows, (v(-0.06, 1.600, 0.080), v(0.06, 1.624, 0.110)), 0.0010, HAIR, "hair"))

    # ---------------- mata: bola mata, iris, pupil (menghadap +Z)
    for sg in (1.0, -1.0):
        ec = v(sg * 0.031, 1.594, 0.0745)
        P.append(Part(f"eye_white_{'L' if sg > 0 else 'R'}", [Prim(lambda p, ec=ec: sd_ellipsoid(p, ec, (0.0118, 0.0118, 0.0118)), "Head")],
                      (ec - 0.016, ec + 0.016), 0.0011, EYE_WHITE, "eye"))
        P.append(Part(f"iris_{'L' if sg > 0 else 'R'}", [Prim(lambda p, ec=ec: sd_ellipsoid(p, ec + v(0, 0, 0.0108), (0.0060, 0.0060, 0.0016)), "Head")],
                      (ec + v(-0.009, -0.009, 0.006), ec + v(0.009, 0.009, 0.016)), 0.00045, IRIS, "eye"))
        P.append(Part(f"pupil_{'L' if sg > 0 else 'R'}", [Prim(lambda p, ec=ec: sd_ellipsoid(p, ec + v(0, 0, 0.0121), (0.0027, 0.0027, 0.0009)), "Head")],
                      (ec + v(-0.005, -0.005, 0.009), ec + v(0.005, 0.005, 0.016)), 0.0003, PUPIL, "eye"))

    # ---------------- tangan: telapak + 5 jari x 3 ruas
    for s in ("L", "R"):
        wr = jp[f"Hand.{s}"]
        u, t, n = hand_frame(s)
        R = rot_cols(u, t, n)  # sumbu lokal: x=jari, y=ibu jari, z=normal telapak
        pr = [
            Prim(lambda p, wr=wr, R=R, u=u, n=n: sd_ellipsoid(p, wr + u * 0.052 - n * 0.002, (0.050, 0.040, 0.0118), R), f"Hand.{s}", tag="palm"),
            Prim(lambda p, wr=wr, u=u: sd_round_cone(p, wr - u * 0.012, wr + u * 0.018, 0.026, 0.024), f"Hand.{s}", 0.012, tag="wrist"),
            Prim(lambda p, wr=wr, R=R, u=u, t=t, n=n: sd_ellipsoid(p, wr + u * 0.034 + t * 0.024 + n * 0.004, (0.022, 0.013, 0.011), R), f"Hand.{s}", 0.010, tag="thenar"),
        ]
        for fname in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
            pts, d, (r0, r1) = finger_chain(s, fname, wr)
            rs = np.linspace(r0, r1, 4)
            for i in range(3):
                pr.append(Prim(lambda p, a=pts[i], b=pts[i + 1], ra=rs[i], rb=rs[i + 1]: sd_round_cone(p, a, b, ra, rb),
                               f"{fname}{i + 1}.{s}", 0.004 if i else 0.012, tag=f"{fname.lower()}{i + 1}"))
        pts_all = np.array([wr - u * 0.03] + [q for f in ("Thumb", "Index", "Middle", "Ring", "Pinky") for q in finger_chain(s, f, wr)[0]])
        lo, hi = pts_all.min(0) - 0.03, pts_all.max(0) + 0.03
        P.append(Part(f"hand_{s}", pr, (lo, hi), 0.0021, SKIN, "skin",
                      allowed={f"Hand.{s}", f"LowerArm.{s}"} | {f"{f}{i}.{s}" for f in ("Thumb", "Index", "Middle", "Ring", "Pinky") for i in (1, 2, 3)}))
    return P


# ---------------------------------------------------------------- mesh + skin
def mesh_part(part: Part):
    lo, hi = part.bounds
    st = part.step
    xs = np.arange(lo[0], hi[0] + st, st)
    ys = np.arange(lo[1], hi[1] + st, st)
    zs = np.arange(lo[2], hi[2] + st, st)
    G = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1).reshape(-1, 3)
    d = np.empty(len(G))
    for i in range(0, len(G), 400_000):
        d[i:i + 400_000] = part.sdf(G[i:i + 400_000])
    vol = d.reshape(len(xs), len(ys), len(zs))
    if vol.min() > 0 or vol.max() < 0:
        raise RuntimeError(f"{part.name}: permukaan tidak ditemukan di grid")
    verts, faces, _, _ = marching_cubes(vol, level=0.0, spacing=(st, st, st))
    verts += lo
    # normal dari gradien SDF (halus)
    e = st * 0.5
    grad = np.zeros_like(verts)
    for ax in range(3):
        dv = np.zeros(3)
        dv[ax] = e
        grad[:, ax] = part.sdf(verts + dv) - part.sdf(verts - dv)
    normals = grad / np.maximum(np.linalg.norm(grad, axis=1, keepdims=True), 1e-12)
    # marching_cubes skimage: urutan segitiga mengikuti gradien; pastikan normal geometri searah normal SDF
    tri = verts[faces]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    if np.mean(np.einsum("ij,ij->i", fn, normals[faces].mean(1))) < 0:
        faces = faces[:, ::-1]
    return verts.astype(np.float64), normals, faces.astype(np.uint32)


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, ab)), axis=1)


def skin_weights(part: Part, verts: np.ndarray, J: dict[str, Joint], names: list[str]):
    _, dists = part.sdf(verts, per_prim=True)
    unions = [pr for pr in part.prims if pr.op == "union"]
    region = np.argmin(np.stack(dists, 1), axis=1)
    children: dict[str, list[str]] = {}
    for j in J.values():
        if j.parent:
            children.setdefault(j.parent, []).append(j.name)
    W = np.zeros((len(verts), len(names)))
    for ri, pr in enumerate(unions):
        idx = np.where(region == ri)[0]
        if not len(idx):
            continue
        cand = {pr.bone, J[pr.bone].parent, *children.get(pr.bone, [])} - {None, "Root"}
        if part.allowed is not None:
            cand &= part.allowed | {pr.bone}
        if pr.bone == "Head" or part.name.startswith(("eye", "iris", "pupil", "hair")):
            cand = {"Head"} if part.name != "skin_body" else cand
        pts = verts[idx]
        cols, ws = [], []
        for b in cand:
            dd = seg_dist(pts, J[b].pos, J[b].tail)
            cols.append(names.index(b))
            ws.append(1.0 / np.maximum(dd, 0.004) ** 7)
        ws = np.stack(ws, 1)
        ws /= ws.sum(1, keepdims=True)
        W[np.ix_(idx, cols)] = ws
    # 4 pengaruh teratas, kuantisasi uint8 yang jumlahnya tepat 255
    top = np.argsort(-W, axis=1)[:, :4]
    tw = np.take_along_axis(W, top, 1)
    tw /= np.maximum(tw.sum(1, keepdims=True), 1e-12)
    q = np.floor(tw * 255).astype(int)
    q[np.arange(len(q)), 0] += 255 - q.sum(1)
    top = np.where(q > 0, top, 0)
    return top.astype(np.uint8), q.astype(np.uint8)


def vertex_colors(part: Part, verts):
    c = np.tile(np.array(part.color + (255,), dtype=np.float64), (len(verts), 1))
    for fn, col, width in part.tint:
        dd = fn(verts)
        a = np.clip(1.0 - dd / width, 0, 1)[:, None]
        c[:, :3] = c[:, :3] * (1 - a) + np.array(col) * a
    if part.material == "skin":  # sedikit variasi warna kulit agar tidak datar
        y = verts[:, 1]
        c[:, :3] *= (0.97 + 0.03 * np.clip((y - 0.0) / 1.7, 0, 1))[:, None]
    return np.clip(c, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- glTF
class GLB:
    def __init__(self):
        self.bin = bytearray()
        self.views, self.accessors = [], []

    def _view(self, data: bytes, target=None) -> int:
        while len(self.bin) % 4:
            self.bin += b"\0"
        off = len(self.bin)
        self.bin += data
        vw = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            vw["target"] = target
        self.views.append(vw)
        return len(self.views) - 1

    def acc(self, arr: np.ndarray, typ: str, ctype: int, normalized=False, target=None, minmax=False) -> int:
        arr = np.ascontiguousarray(arr)
        view = self._view(arr.tobytes(), target)
        a = {"bufferView": view, "componentType": ctype, "count": int(arr.shape[0]), "type": typ}
        if normalized:
            a["normalized"] = True
        if minmax:
            flat = arr.reshape(arr.shape[0], -1)
            a["min"] = [float(x) for x in flat.min(0)]
            a["max"] = [float(x) for x in flat.max(0)]
        self.accessors.append(a)
        return len(self.accessors) - 1


F32, U8, U16, U32 = 5126, 5121, 5123, 5125

MATERIALS = {
    "skin": {"name": "kulit", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0.0, "roughnessFactor": 0.62}},
    "cloth": {"name": "kain", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0.0, "roughnessFactor": 0.92}},
    "hair": {"name": "rambut", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0.0, "roughnessFactor": 0.55}},
    "eye": {"name": "mata", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0.0, "roughnessFactor": 0.18}},
}


def write_glb(path: str, J: dict[str, Joint], meshes: list[dict], animations: list[dict], extras: dict) -> dict:
    g = GLB()
    names = list(J.keys())
    nodes = []
    for nm in names:
        j = J[nm]
        local = j.pos - (J[j.parent].pos if j.parent else 0)
        nodes.append({"name": nm, "translation": [round(float(x), 6) for x in local]})
    for nm in names:
        kids = [names.index(c) for c, j in J.items() if j.parent == nm]
        if kids:
            nodes[names.index(nm)]["children"] = kids
    ibm = np.zeros((len(names), 16), np.float32)
    for i, nm in enumerate(names):
        m = np.eye(4)
        m[:3, 3] = -J[nm].pos
        ibm[i] = m.T.reshape(-1)  # kolom-mayor
    ibm_acc = g.acc(ibm, "MAT4", F32)
    mat_keys = list(MATERIALS)
    gl_meshes = []
    mesh_nodes = []
    for m in meshes:
        attrs = {
            "POSITION": g.acc(m["pos"].astype(np.float32), "VEC3", F32, target=34962, minmax=True),
            "NORMAL": g.acc(m["nrm"].astype(np.float32), "VEC3", F32, target=34962),
            "COLOR_0": g.acc(m["col"], "VEC4", U8, normalized=True, target=34962),
            "JOINTS_0": g.acc(m["jnt"], "VEC4", U8, target=34962),
            "WEIGHTS_0": g.acc(m["wgt"], "VEC4", U8, normalized=True, target=34962),
        }
        idx = m["idx"].reshape(-1)
        ind = g.acc(idx.astype(np.uint16) if idx.max() < 65535 else idx.astype(np.uint32), "SCALAR",
                    U16 if idx.max() < 65535 else U32, target=34963)
        gl_meshes.append({"name": m["name"], "primitives": [{"attributes": attrs, "indices": ind, "material": mat_keys.index(m["material"])}],
                          "extras": m.get("extras", {})})
        nodes.append({"name": f"mesh_{m['name']}", "mesh": len(gl_meshes) - 1, "skin": 0})
        mesh_nodes.append(len(nodes) - 1)
    gl_anims = []
    for an in animations:
        samplers, channels = [], []
        for tr in an["tracks"]:
            t_acc = g.acc(tr["times"].astype(np.float32), "SCALAR", F32, minmax=True)
            o_acc = g.acc(tr["values"].astype(np.float32), "VEC4" if tr["path"] == "rotation" else "VEC3", F32)
            samplers.append({"input": t_acc, "output": o_acc, "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1, "target": {"node": names.index(tr["joint"]), "path": tr["path"]}})
        gl_anims.append({"name": an["name"], "samplers": samplers, "channels": channels, "extras": an.get("extras", {})})
    doc = {
        "asset": {"version": "2.0", "generator": f"SILATARA build_character.py {CHARACTER_VERSION}", "copyright": "SILATARA — dibuat prosedural; tanpa aset pihak ketiga"},
        "scene": 0, "scenes": [{"name": "instruktur", "nodes": [0] + mesh_nodes}],
        "nodes": nodes, "meshes": gl_meshes,
        "skins": [{"name": "rig", "joints": list(range(len(names))), "inverseBindMatrices": ibm_acc, "skeleton": 0}],
        "materials": [MATERIALS[k] for k in mat_keys], "animations": gl_anims,
        "accessors": g.accessors, "bufferViews": g.views, "buffers": [{"byteLength": len(g.bin)}], "extras": extras,
    }
    js = json.dumps(doc, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    while len(g.bin) % 4:
        g.bin += b"\0"
    total = 12 + 8 + len(js) + 8 + len(g.bin)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(g.bin), 0x004E4942) + bytes(g.bin))
    return {"bytes": total, "meshes": len(gl_meshes), "joints": len(names), "animations": len(gl_anims)}


def build_meshes(J):
    names = list(J.keys())
    out = []
    for part in build_parts(J):
        vs, ns, fs = mesh_part(part)
        jn, wt = skin_weights(part, vs, J, names)
        col = vertex_colors(part, vs)
        feats = sorted({pr.tag for pr in part.prims if pr.tag})
        out.append({"name": part.name, "pos": vs, "nrm": ns, "idx": fs, "jnt": jn, "wgt": wt, "col": col,
                    "material": part.material, "extras": {"features": feats}})
    return out
