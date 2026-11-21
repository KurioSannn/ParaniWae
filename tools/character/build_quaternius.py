"""Karakter 3D SILATARA dari model berlisensi terbuka: Quaternius "Universal Base Characters" (CC0 1.0).

Langkah: muat glTF (Superhero Male) -> tambah rambut (statis, dipasang ke tulang Head) -> buat baju & celana latihan dari
permukaan tubuh yang sama (offset sepanjang normal, bobot skin disalin sehingga ikut rig) -> pindahkan (retarget) semua klip
gerak bersumber (animate.py, rig SILATARA) ke rig UE 65 sendi -> validasi -> tulis GLB tunggal.

Retarget memakai rotasi delta dunia dari rig sumber: batang tubuh/kepala memakai delta apa adanya; lengan, tangan, jari
dikoreksi terhadap perbedaan pose istirahat (A-pose vs T-pose); tungkai diselesaikan IK dua ruas ke posisi pergelangan kaki
sumber sehingga telapak tidak meluncur.

Pemakaian: python tools/character/build_quaternius.py <folder-paket-ubc> [--out content/pencak-silat/character]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import struct
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import animate as an  # noqa: E402
import build_character as bc  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ANIM = ROOT / "content/pencak-silat/animations"
VERSION = "2.0.0"
ARM_EXTRA_ABD_DEG = 7.0     # tubuh Superhero lebih lebar dari rig sumber: lengan dibuka sedikit agar tidak menembus
CLOTH_SHIRT, CLOTH_PANTS, CLOTH_SASH = 0.0105, 0.0085, 0.019
CLOTH_RGB = (0.118, 0.231, 0.196)   # #1E3B32 (forest-900)
SASH_RGB = (0.725, 0.522, 0.31)     # #B9854F (bronze-500), polos tanpa tanda tingkatan

F32, U8, U16, U32 = 5126, 5121, 5123, 5125


# ---------------------------------------------------------------- util matematika
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def unit(a):
    n = np.linalg.norm(a)
    return a / n if n > 1e-12 else a


def align(a, b):
    return an.align(unit(a), unit(b))


def rz(a):
    return an.rz(a)


# ---------------------------------------------------------------- glTF sederhana
class Gltf:
    def __init__(self, path: Path):
        self.dir = path.parent
        self.j = json.loads(path.read_text(encoding="utf-8"))
        self.bin = bytearray((self.dir / self.j["buffers"][0]["uri"]).read_bytes())

    def acc(self, i: int) -> np.ndarray:
        a = self.j["accessors"][i]
        v = self.j["bufferViews"][a["bufferView"]]
        ct = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8, 5122: np.int16, 5120: np.int8}[a["componentType"]]
        n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride")
        itemsize = np.dtype(ct).itemsize * n
        if stride and stride != itemsize:
            raw = np.frombuffer(self.bin, dtype=np.uint8, count=a["count"] * stride, offset=off).reshape(a["count"], stride)[:, :itemsize]
            return np.ascontiguousarray(raw).view(ct).reshape(a["count"], n)
        return np.frombuffer(self.bin, dtype=ct, count=a["count"] * n, offset=off).reshape(a["count"], n).copy()


PACK_ROOT: Path | None = None


def resolve_image(path: Path) -> Path:
    """Beberapa URI di glTF Quaternius menunjuk '<nama>_png.png' yang tidak ada di paket; cari berkas setara."""
    if path.exists():
        return path
    for cand in (path.with_name(path.name.replace("_png.png", ".png")), path.with_name(path.name.replace(".png", "_png.png"))):
        if cand.exists():
            return cand
    if PACK_ROOT is not None:
        for stem in (path.name, path.name.replace("_png.png", ".png")):
            hit = next(PACK_ROOT.rglob(stem), None)
            if hit:
                return hit
    raise FileNotFoundError(path)


def image_bytes(path: Path) -> tuple[bytes, str]:
    """Kecilkan & kompres tekstur: warna 2048 -> JPEG, normal/roughness 1024 -> JPEG, tekstur kecil tetap PNG."""
    path = resolve_image(path)
    im = Image.open(path)
    name = path.name.lower()
    big = max(im.size) >= 1024
    if big:
        target = 2048 if any(k in name for k in ("basecolor", "dark", "male", "female")) and not any(k in name for k in ("normal", "roughness")) else 1024
        if max(im.size) > target:
            im = im.resize((target, target), Image.LANCZOS)
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=90 if "normal" not in name else 92, optimize=True)
        return buf.getvalue(), "image/jpeg"
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue(), "image/png"


class Builder:
    """Perakit GLB: menampung JSON + satu buffer biner gabungan."""

    def __init__(self, base: Gltf):
        self.j = base.j
        self.bin = bytearray(base.bin)
        self.src_dir = base.dir
        self.j["buffers"] = [{"byteLength": 0}]
        self._embed_images(self.j, self.src_dir)

    def view(self, data: bytes, target=None) -> int:
        while len(self.bin) % 4:
            self.bin += b"\0"
        self.j["bufferViews"].append({"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data), **({"target": target} if target else {})})
        self.bin += data
        return len(self.j["bufferViews"]) - 1

    def accessor(self, arr: np.ndarray, typ: str, ctype: int, target=None, minmax=False, normalized=False) -> int:
        arr = np.ascontiguousarray(arr)
        a = {"bufferView": self.view(arr.tobytes(), target), "componentType": ctype, "count": int(arr.shape[0]), "type": typ}
        if normalized:
            a["normalized"] = True
        if minmax:
            flat = arr.reshape(arr.shape[0], -1)
            a["min"], a["max"] = [float(x) for x in flat.min(0)], [float(x) for x in flat.max(0)]
        self.j["accessors"].append(a)
        return len(self.j["accessors"]) - 1

    def _embed_images(self, j, d: Path):
        """Dipanggil untuk glTF dasar (bufferView sudah ada di self.bin)."""
        for im in j.get("images", []):
            if "uri" in im:
                data, mime = image_bytes(d / im["uri"])
                im.pop("uri")
                im["bufferView"], im["mimeType"] = self.view(data), mime

    def append(self, other: Gltf) -> dict:
        """Tambahkan semua buffer/accessor/mesh/material/tekstur dari glTF lain. Mengembalikan peta indeks mesh baru."""
        o = other.j
        shift = len(self.bin)
        while shift % 4:
            self.bin += b"\0"
            shift += 1
        base_bv = len(self.j["bufferViews"])
        self.bin += other.bin
        for v in o["bufferViews"]:
            v2 = dict(v)
            v2["buffer"], v2["byteOffset"] = 0, v.get("byteOffset", 0) + shift
            self.j["bufferViews"].append(v2)
        a0 = len(self.j["accessors"])
        for a in o["accessors"]:
            a2 = dict(a)
            a2["bufferView"] = a["bufferView"] + base_bv
            self.j["accessors"].append(a2)
        im0 = len(self.j["images"])
        for im in o.get("images", []):
            data, mime = image_bytes(other.dir / im["uri"])
            self.j["images"].append({"name": im.get("name", im["uri"]), "bufferView": self.view(data), "mimeType": mime})
        s0 = len(self.j.setdefault("samplers", []))
        self.j["samplers"] += o.get("samplers", [])
        t0 = len(self.j["textures"])
        for t in o.get("textures", []):
            t2 = {"source": t["source"] + im0}
            if "sampler" in t:
                t2["sampler"] = t["sampler"] + s0
            self.j["textures"].append(t2)
        m0 = len(self.j["materials"])
        for m in o.get("materials", []):
            m2 = json.loads(json.dumps(m))

            def fix(d):
                for k, v in list(d.items()):
                    if isinstance(v, dict):
                        if "index" in v and k.endswith("Texture"):
                            v["index"] += t0
                        fix(v)
            fix(m2)
            self.j["materials"].append(m2)
        me0 = len(self.j["meshes"])
        for me in o["meshes"]:
            me2 = json.loads(json.dumps(me))
            for p in me2["primitives"]:
                p["attributes"] = {k: v + a0 for k, v in p["attributes"].items()}
                if "indices" in p:
                    p["indices"] += a0
                p["material"] = p.get("material", 0) + m0
            self.j["meshes"].append(me2)
        return {"mesh0": me0, "material0": m0}

    def write(self, path: Path):
        self.j["buffers"][0]["byteLength"] = len(self.bin)
        js = json.dumps(self.j, separators=(",", ":")).encode()
        js += b" " * ((4 - len(js) % 4) % 4)
        while len(self.bin) % 4:
            self.bin += b"\0"
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, total))
            f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
            f.write(struct.pack("<II", len(self.bin), 0x004E4942) + bytes(self.bin))
        return total


# ---------------------------------------------------------------- data rig target
class TargetRig:
    def __init__(self, j: dict):
        self.nodes = j["nodes"]
        self.skin = j["skins"][0]
        self.idx = {n["name"]: i for i, n in enumerate(self.nodes)}
        self.parent = {}
        for i, n in enumerate(self.nodes):
            for c in n.get("children", []):
                self.parent[c] = i
        joints = set(self.skin["joints"])
        self.names = [self.nodes[i]["name"] for i in self.skin["joints"]]
        self.par_name = {self.nodes[i]["name"]: (self.nodes[self.parent[i]]["name"] if self.parent.get(i) in joints else None) for i in self.skin["joints"]}
        self.WR, self.WP, self.W4 = {}, {}, {}
        for i in range(len(self.nodes)):
            self._world(i)
        self.rest_pos = {n: self.W4[self.idx[n]][:3, 3] for n in self.names}
        self.rest_rot = {n: self.WR[self.idx[n]] for n in self.names}
        self.children = {n: [c for c in self.names if self.par_name[c] == n] for n in self.names}
        # urutan induk -> anak
        self.order = []
        todo = [n for n in self.names if self.par_name[n] is None]
        while todo:
            n = todo.pop(0)
            self.order.append(n)
            todo += self.children[n]

    def _world(self, i):
        if i in self.W4:
            return self.W4[i]
        n = self.nodes[i]
        M = np.eye(4)
        M[:3, :3] = qmat(n.get("rotation", [0, 0, 0, 1])) * np.array(n.get("scale", [1, 1, 1]))
        M[:3, 3] = n.get("translation", [0, 0, 0])
        W = self._world(self.parent[i]) @ M if i in self.parent else M
        self.W4[i] = W
        self.WR[i] = qmat(n.get("rotation", [0, 0, 0, 1])) if i not in self.parent else self.WR[self.parent[i]] @ qmat(n.get("rotation", [0, 0, 0, 1]))
        return W


SRC_OF = {"pelvis": "Hips", "spine_01": "Spine", "spine_02": "Spine", "spine_03": "Chest", "neck_01": "Neck", "Head": "Head"}
FINGERS = ("thumb", "index", "middle", "ring", "pinky")
SRC_FINGER = {"thumb": "Thumb", "index": "Index", "middle": "Middle", "ring": "Ring", "pinky": "Pinky"}
for s_, S_ in (("l", "L"), ("r", "R")):
    SRC_OF.update({f"clavicle_{s_}": f"Clavicle.{S_}", f"upperarm_{s_}": f"UpperArm.{S_}", f"lowerarm_{s_}": f"LowerArm.{S_}", f"hand_{s_}": f"Hand.{S_}",
                   f"thigh_{s_}": f"UpperLeg.{S_}", f"calf_{s_}": f"LowerLeg.{S_}", f"foot_{s_}": f"Foot.{S_}", f"ball_{s_}": f"Toes.{S_}"})
    for f in FINGERS:
        for i in (1, 2, 3):
            SRC_OF[f"{f}_0{i}_{s_}"] = f"{SRC_FINGER[f]}{i}.{S_}"
USE_Q = {b for b in SRC_OF if b.split("_")[0] in ("clavicle", "upperarm", "lowerarm", "hand") or b.split("_")[0] in FINGERS}


def q_child(rig: TargetRig, b: str) -> str | None:
    kids = rig.children[b]
    pref = {"hand_l": "middle_01_l", "hand_r": "middle_01_r"}
    if b in pref:
        return pref[b]
    return kids[0] if kids else None


def retarget_frame(rig: TargetRig, J, fr, q_corr, arm_abd) -> tuple[dict, np.ndarray, dict]:
    """Rotasi delta dunia R[b] untuk semua tulang target + posisi pelvis + posisi dunia sendi."""
    R: dict[str, np.ndarray] = {}
    P: dict[str, np.ndarray] = {}
    info = {"ik_clamp": 0}
    pelvis = rig.rest_pos["pelvis"] + (fr["hips"] - J["Hips"].pos)
    for b in rig.order:
        p = rig.par_name[b]
        if b == "root":
            R[b], P[b] = np.eye(3), rig.rest_pos[b].copy()
            continue
        # posisi
        if b == "pelvis":
            P[b] = pelvis
        else:
            P[b] = P[p] + R[p] @ (rig.rest_pos[b] - rig.rest_pos[p])
        # rotasi
        s = SRC_OF.get(b)
        if s is None:
            R[b] = R[p]  # tulang daun / tidak dipetakan: ikut induk
            continue
        d = fr["G"][s]
        if b in USE_Q:
            side = 1.0 if b.endswith("_l") else -1.0
            R[b] = rz(side * math.radians(arm_abd)) @ d @ q_corr[b]
        else:
            R[b] = d
    # ---- kaki: IK dua ruas ke pergelangan sumber
    for side, S in (("l", "L"), ("r", "R")):
        th, ca, fo = f"thigh_{side}", f"calf_{side}", f"foot_{side}"
        H = P[th]
        A = rig.rest_pos[fo] + (fr["pos"][f"Foot.{S}"] - J[f"Foot.{S}"].pos)
        L1 = np.linalg.norm(rig.rest_pos[ca] - rig.rest_pos[th])
        L2 = np.linalg.norm(rig.rest_pos[fo] - rig.rest_pos[ca])
        dv = A - H
        dist = np.linalg.norm(dv)
        if dist > L1 + L2 - 1e-4:
            info["ik_clamp"] += 1
            dist = L1 + L2 - 1e-4
            A = H + unit(dv) * dist
        dn = unit(dv)
        Ks, Hs, As = fr["pos"][f"LowerLeg.{S}"], fr["pos"][f"UpperLeg.{S}"], fr["pos"][f"Foot.{S}"]
        pole = Ks - (Hs + As) / 2
        pole = pole - dn * np.dot(pole, dn)
        if np.linalg.norm(pole) < 1e-4:
            pole = np.array([0.0, 0.0, 1.0]) - dn * dn[2]
        pole = unit(pole)
        alpha = math.acos(max(-1.0, min(1.0, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist))))
        K = H + L1 * (math.cos(alpha) * dn + math.sin(alpha) * pole)
        d1, d2 = unit(K - H), unit(A - K)
        base_t, base_c = R[th], R[ca]
        R[th] = align(base_t @ unit(rig.rest_pos[ca] - rig.rest_pos[th]), d1) @ base_t
        P[ca] = H + R[th] @ (rig.rest_pos[ca] - rig.rest_pos[th])
        R[ca] = align(base_c @ unit(rig.rest_pos[fo] - rig.rest_pos[ca]), d2) @ base_c
        P[fo] = P[ca] + R[ca] @ (rig.rest_pos[fo] - rig.rest_pos[ca])
        info[f"ankle_err_{side}"] = float(np.linalg.norm(P[fo] - (rig.rest_pos[fo] + (fr["pos"][f"Foot.{S}"] - J[f"Foot.{S}"].pos))))
        # turunan kaki mengikuti
        for b in rig.order:
            if rig.par_name[b] in (fo,) or (rig.par_name[b] in (f"ball_{side}",)):
                pp = rig.par_name[b]
                P[b] = P[pp] + R[pp] @ (rig.rest_pos[b] - rig.rest_pos[pp])
        P[f"ball_{side}"] = P[fo] + R[fo] @ (rig.rest_pos[f"ball_{side}"] - rig.rest_pos[fo])
    return R, pelvis, {"P": P, **info}


def compute_q_corr(rig: TargetRig, J) -> dict:
    """Koreksi pose istirahat (target T-pose vs sumber A-pose) untuk lengan, tangan, jari."""
    out = {}
    for b in USE_Q:
        c = q_child(rig, b)
        if c is None:
            out[b] = np.eye(3)
            continue
        d_t = unit(rig.rest_pos[c] - rig.rest_pos[b])
        s = SRC_OF[b]
        d_s = unit(J[s].tail - J[s].pos)
        out[b] = align(d_t, d_s)
    return out


# ---------------------------------------------------------------- pakaian dari permukaan tubuh
def build_clothing(g: Gltf, rig: TargetRig):
    body_mesh = next(m for m in g.j["meshes"] if m["name"].startswith("Sphere"))
    prim = body_mesh["primitives"][0]
    P = g.acc(prim["attributes"]["POSITION"]).astype(np.float64)
    Nn = g.acc(prim["attributes"]["NORMAL"]).astype(np.float64)
    Jt = g.acc(prim["attributes"]["JOINTS_0"]).astype(int)
    Wt = g.acc(prim["attributes"]["WEIGHTS_0"]).astype(np.float64)
    F = g.acc(prim["indices"]).astype(np.int64).reshape(-1, 3)
    joint_names = rig.names
    dom = np.array([joint_names[Jt[i, np.argmax(Wt[i])]] for i in range(len(P))])
    y = P[:, 1]

    def region(names, extra=None):
        m = np.isin(dom, list(names))
        return m if extra is None else m & extra
    # lengan baju berhenti ~90% lengan bawah (pergelangan telanjang)
    sleeve_ok = np.ones(len(P), bool)
    for s in ("l", "r"):
        el, wr = rig.rest_pos[f"lowerarm_{s}"], rig.rest_pos[f"hand_{s}"]
        axis = unit(wr - el)
        t = ((P - el) @ axis) / np.linalg.norm(wr - el)
        sleeve_ok &= ~((dom == f"lowerarm_{s}") & (t > 0.90))
    shirt = region({"spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r"}, sleeve_ok) \
        | ((dom == "pelvis") & (y > 0.93)) | ((dom == "neck_01") & (y < 1.505))
    # celana mencakup seluruh pelvis (tumpang tindih dengan baju di pinggang) agar tidak ada celah segitiga di sambungan
    pants = region({"pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r"}, y > 0.115)

    jn = np.array(joint_names)

    def group_w(group):
        gm = np.isin(jn, list(group))
        return (Wt * gm[Jt]).sum(axis=1)
    w_arm = group_w({"upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r"})
    w_torso = group_w({"spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r"})
    w_leg = group_w({"thigh_l", "thigh_r", "calf_l", "calf_r"})
    # potongan longgar: baju latihan agak lapang di lengan & badan, celana gombrong di tungkai
    shirt_off = CLOTH_SHIRT + 0.006 * w_torso + 0.011 * w_arm
    pants_off = CLOTH_PANTS + 0.017 * w_leg

    def make(mask, off):
        keep = mask[F].all(axis=1)
        faces = F[keep]
        used = np.unique(faces)
        remap = -np.ones(len(P), int)
        remap[used] = np.arange(len(used))
        o = off[used][:, None] if np.ndim(off) else off
        return {"pos": P[used] + Nn[used] * o, "nrm": Nn[used], "joints": Jt[used], "wgt": Wt[used], "idx": remap[faces], "src": used}
    shirt_m, pants_m = make(shirt, shirt_off), make(pants, pants_off)
    # sabuk: pita sempit di pinggang
    band = (y > 1.025) & (y < 1.085) & (dom != "thigh_l") & (dom != "thigh_r")
    sash_m = make(band & (shirt | pants), CLOTH_SASH + 0.006 * w_torso)
    return {"shirt": shirt_m, "pants": pants_m, "sash": sash_m}, (P, Nn, Jt, Wt, F, dom)


def add_cloth_nodes(b: Builder, rig: TargetRig, parts: dict, parent_idx: int) -> dict:
    mats = {"kain": {"name": "kain", "doubleSided": True, "pbrMetallicRoughness": {"baseColorFactor": [*CLOTH_RGB, 1], "metallicFactor": 0, "roughnessFactor": 0.92}},
            "sabuk": {"name": "sabuk", "doubleSided": True, "pbrMetallicRoughness": {"baseColorFactor": [*SASH_RGB, 1], "metallicFactor": 0, "roughnessFactor": 0.85}}}
    mi = {}
    for k, m in mats.items():
        b.j["materials"].append(m)
        mi[k] = len(b.j["materials"]) - 1
    info = {}
    for name, key in (("Baju", "shirt"), ("Celana", "pants"), ("Sabuk", "sash")):
        p = parts[key]
        if len(p["idx"]) == 0:
            continue
        attrs = {"POSITION": b.accessor(p["pos"].astype(np.float32), "VEC3", F32, 34962, True),
                 "NORMAL": b.accessor(p["nrm"].astype(np.float32), "VEC3", F32, 34962),
                 "JOINTS_0": b.accessor(p["joints"].astype(np.uint8), "VEC4", U8, 34962),
                 "WEIGHTS_0": b.accessor(p["wgt"].astype(np.float32), "VEC4", F32, 34962)}
        ind = b.accessor(p["idx"].reshape(-1).astype(np.uint32), "SCALAR", U32, 34963)
        b.j["meshes"].append({"name": name, "primitives": [{"attributes": attrs, "indices": ind, "material": mi["sabuk" if key == "sash" else "kain"]}]})
        b.j["nodes"].append({"name": name, "mesh": len(b.j["meshes"]) - 1, "skin": 0})
        b.j["nodes"][parent_idx].setdefault("children", []).append(len(b.j["nodes"]) - 1)
        info[name] = {"vertices": int(len(p["pos"])), "triangles": int(len(p["idx"]))}
    return info


def attach_hair(b: Builder, rig: TargetRig, hair_path: Path, head_name="Head"):
    h = Gltf(hair_path)
    ids = b.append(h)
    hn = rig.idx[head_name]
    Wh = rig.W4[hn]
    Rh = Wh[:3, :3]
    local_t = -(Rh.T @ Wh[:3, 3])
    q = an.mat_to_quat(Rh.T)
    b.j["nodes"].append({"name": "Rambut", "mesh": ids["mesh0"], "translation": [float(x) for x in local_t], "rotation": [float(x) for x in q]})
    b.j["nodes"][hn].setdefault("children", []).append(len(b.j["nodes"]) - 1)
    return {"mesh": h.j["meshes"][0]["name"]}


# ---------------------------------------------------------------- klip
def load_specs():
    out = []
    for d in sorted(ANIM.iterdir()):
        kf = d / "keyframes.json"
        if kf.exists():
            s = json.loads(kf.read_text(encoding="utf-8"))
            if s.get("animation_status") == "generated" and s.get("view") in ("side", "front"):
                out.append(s)
    idle = {"movement_id": "idle", "animation_id": "anim.idle.v1", "title": "Sikap siap (diam)", "view": "front", "source_ids": [],
            "keyframes": [{"id": "i1", "label": "Siap", "pose": {"arms": {"L": [10, 6], "R": [10, 6]}, "hands": {"L": "open", "R": "open"}}},
                          {"id": "i2", "label": "Siap", "pose": {"arms": {"L": [11, 8], "R": [11, 8]}, "head": 1.5, "hands": {"L": "open", "R": "open"}}}],
            "sequence": [{"pose": "i1", "hold_ms": 600}, {"pose": "i2", "move_ms": 1600, "hold_ms": 300}], "return_ms": 1600}
    return [idle, *out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pack")
    ap.add_argument("--out", default=str(ROOT / "content/pencak-silat/character"))
    ap.add_argument("--clips", default="")
    ap.add_argument("--hair", default="Hair_SimpleParted")
    a = ap.parse_args()
    t0 = time.time()
    global PACK_ROOT
    pack = Path(a.pack)
    PACK_ROOT = pack
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    body_path = pack / "Base Characters/Godot - UE/Superhero_Male_FullBody.gltf"
    base = Gltf(body_path)
    rig = TargetRig(base.j)
    J = bc.build_rig()
    an.J_TAIL.update({k: j.tail for k, j in J.items()})
    an.J_POS.update({k: j.pos for k, j in J.items()})
    poser = an.Poser(J)
    q_corr = compute_q_corr(rig, J)

    parts, body = build_clothing(base, rig)
    armature_parent = rig.parent[next(i for i, n in enumerate(base.j["nodes"]) if n.get("mesh") is not None)]
    b = Builder(base)
    cloth_info = add_cloth_nodes(b, rig, parts, armature_parent)
    hair_info = attach_hair(b, rig, pack / f"Hairstyles/Origin at 0/glTF (Godot)/{a.hair}.gltf")
    for m in b.j["materials"]:
        if m.get("name") == "MI_Hair_1":  # tekstur rambut Quaternius abu-abu; dikalikan warna gelap -> hitam kecokelatan
            m["pbrMetallicRoughness"]["baseColorFactor"] = [0.20, 0.15, 0.12, 1.0]
    print(f"model+pakaian+rambut siap ({time.time() - t0:.1f}s)", cloth_info, flush=True)

    # ---- klip
    specs = load_specs()
    if a.clips:
        wanted = set(a.clips.split(","))
        specs = [s for s in specs if s["movement_id"] in wanted or s["movement_id"] == "idle"]
    P0, N0, Jt0, Wt0, F0, dom0 = body
    names = rig.names
    joint_idx = {n: i for i, n in enumerate(names)}
    torso_v = np.where(np.isin(dom0, ["spine_01", "spine_02", "spine_03", "pelvis", "clavicle_l", "clavicle_r"]))[0]
    hand_v = {s: np.where(np.isin(dom0, [n for n in names if n.endswith(f"_{s}") and n.split("_")[0] in FINGERS + ("hand",)]))[0] for s in ("l", "r")}
    anims, report, clips_meta = [], [], []
    old_meta = {c["clip"]: c for c in json.loads((out / "clips.json").read_text())["clips"]} if (out / "clips.json").exists() else {}

    def skin_verts(R, P, sel):
        v = np.zeros((len(sel), 3))
        for k in range(4):
            jn = np.array([names[i] for i in Jt0[sel, k]])
            w = Wt0[sel, k][:, None]
            Rs = np.stack([R[n] for n in jn])
            Ps = np.stack([P[n] for n in jn])
            Rp = np.stack([rig.rest_pos[n] for n in jn])
            v += w * (np.einsum("nij,nj->ni", Rs, P0[sel] - Rp) + Ps)
        return v

    for spec in specs:
        clip = an.build_clip(poser, spec)
        frames = clip["frames"]
        Rs, pelv, Ps = [], [], []
        ik_err = floor = 9.0
        clamps = 0
        pen_min, slide = 9.0, 0.0
        for i, fr in enumerate(frames):
            R, pel, info = retarget_frame(rig, J, fr, q_corr, ARM_EXTRA_ABD_DEG)
            Rs.append(R)
            pelv.append(pel)
            Ps.append(info["P"])
            clamps += info["ik_clamp"]
            ik_err = max(ik_err if ik_err != 9.0 else 0.0, info["ankle_err_l"], info["ankle_err_r"])
            floor = min(floor, min(info["P"][f"ball_{s}"][1] for s in "lr"), min(info["P"][f"foot_{s}"][1] for s in "lr"))
        # kontak lantai: kaki tumpu tidak meluncur (selisih posisi pergelangan antar frame saat target sama)
        for i in range(1, len(frames)):
            for s_, S in (("l", "L"), ("r", "R")):
                ta, tb = frames[i - 1]["targets"]["ankles"][S], frames[i]["targets"]["ankles"][S]
                if np.allclose(ta, tb) and tb[1] <= bc.ANKLE_Y + 1e-6:
                    slide = max(slide, float(np.linalg.norm(Ps[i][f"foot_{s_}"] - Ps[i - 1][f"foot_{s_}"])))
        # penetrasi tangan-badan (sampling tiap 4 frame)
        for i in range(0, len(frames), 4):
            tv = skin_verts(Rs[i], Ps[i], torso_v[::2])
            tree = cKDTree(tv)
            for s in ("l", "r"):
                hv = skin_verts(Rs[i], Ps[i], hand_v[s][::2])
                pen_min = min(pen_min, float(tree.query(hv)[0].min()))
        loop_dq = max(float(np.max(np.abs(an.mat_to_quat(Rs[0][n]) - an.mat_to_quat(Rs[-1][n])))) for n in names)
        # ---- track: rotasi lokal tiap tulang (+ translasi pelvis)
        times = np.array([f["t"] for f in frames])
        tracks = []
        for n in names:
            if n == "root":
                continue
            p = rig.par_name[n]
            qs = []
            for R in Rs:
                Rp = R[p] if p else np.eye(3)
                loc = rig.rest_rot[p].T @ Rp.T @ R[n] @ rig.rest_rot[n] if p else R[n] @ rig.rest_rot[n]
                q = an.mat_to_quat(loc)
                if qs and np.dot(q, qs[-1]) < 0:
                    q = -q
                qs.append(q)
            qs = np.array(qs)
            keep = an.reduce_keys(times, qs, 0.0006)
            tracks.append({"joint": n, "path": "rotation", "times": times[keep], "values": qs[keep]})
        Wroot_inv = np.linalg.inv(rig.W4[rig.idx["root"]])
        tl = np.array([(Wroot_inv @ np.append(p_, 1))[:3] for p_ in pelv])
        keep = an.reduce_keys(times, tl, 0.0003)
        tracks.append({"joint": "pelvis", "path": "translation", "times": times[keep], "values": tl[keep]})
        ok = ik_err < 0.010 and slide < 0.004 and floor > -0.012 and pen_min > 0.004 and loop_dq < 1e-3
        report.append({"movement_id": spec["movement_id"], "ok": bool(ok), "ankle_err_max_mm": round(ik_err * 1000, 2), "planted_slide_max_mm": round(slide * 1000, 3),
                       "floor_min_mm": round(floor * 1000, 1), "hand_torso_gap_min_mm": round(pen_min * 1000, 1), "loop_quat_maxdiff": round(loop_dq, 6),
                       "ik_clamps": int(clamps), "keys": int(sum(len(t["times"]) for t in tracks))})
        meta = old_meta.get(spec["movement_id"]) or {
            "movement_id": spec["movement_id"], "clip": spec["movement_id"], "animation_id": spec["animation_id"].replace(".v1", ".3d.v1"),
            "source_animation_id": spec["animation_id"], "title": spec.get("title"), "source_view": clip["view"],
            "view_recommendation": "samping" if clip["view"] == "side" else "depan", "source_ids": spec.get("source_ids", [])}
        meta = {**meta, "duration_s": round(clip["duration"], 3), "loop_interval_s": round(clip["duration"], 3), "phases": clip["phases"],
                "validation_status": "generated_checked" if ok else "generated_needs_fix",
                "interpretation": "Tafsir editorial atas uraian sumber; bukan rekaman gerak instruktur. Belum ditinjau instruktur."}
        clips_meta.append(meta)
        anims.append({"name": spec["movement_id"], "tracks": tracks, "extras": {"phases": clip["phases"], "duration_s": meta["duration_s"]}})
        print(f"klip {spec['movement_id']}: {'OK' if ok else 'PERLU PERBAIKAN'} {report[-1]}", flush=True)

    # ---- animasi -> glTF
    for an_ in anims:
        samplers, channels = [], []
        for tr in an_["tracks"]:
            ti = b.accessor(tr["times"].astype(np.float32), "SCALAR", F32, minmax=True)
            oi = b.accessor(tr["values"].astype(np.float32), "VEC4" if tr["path"] == "rotation" else "VEC3", F32)
            samplers.append({"input": ti, "output": oi, "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1, "target": {"node": rig.idx[tr["joint"]], "path": tr["path"]}})
        b.j.setdefault("animations", []).append({"name": an_["name"], "samplers": samplers, "channels": channels, "extras": an_["extras"]})
    b.j["asset"] = {"version": "2.0", "generator": f"SILATARA build_quaternius.py {VERSION}",
                    "copyright": "Model dasar: Quaternius, Universal Base Characters (CC0 1.0). Pakaian, rambut-pasang, dan animasi: SILATARA."}
    b.j["extras"] = {"silatara": {"character_version": VERSION, "clips": [c["clip"] for c in clips_meta]}}
    b.j.pop("cameras", None)
    size = b.write(out / "silatara-instructor.glb")
    digest = hashlib.sha256((out / "silatara-instructor.glb").read_bytes()).hexdigest()
    meshes_meta = [{"name": "Tubuh (Quaternius Superhero Male)", "features": ["kepala", "wajah", "mata", "alis", "telinga", "leher", "badan", "lengan", "tangan 5 jari x 3 ruas", "tungkai", "telapak kaki"]},
                   {"name": "Rambut (Quaternius Hair_SimpleParted)", "features": ["rambut pendek"]},
                   {"name": "Baju, celana, sabuk (SILATARA)", "features": ["baju latihan", "celana latihan", "sabuk polos"]}]
    finger_joints = sum(1 for n in names if n.split("_")[0] in FINGERS and "leaf" not in n)
    character = {
        "schema": "silatara.character/v1", "character_id": "silatara-instruktur-3d", "version": VERSION, "file": "silatara-instructor.glb", "sha256": digest, "bytes": size,
        "format": "glTF 2.0 biner (GLB); skinned mesh, rig UE 65 sendi, material PBR bertekstur (JPEG)", "joints": names, "joint_count": len(names), "finger_joints": finger_joints,
        "meshes": meshes_meta, "units": "meter", "up_axis": "+Y", "forward_axis": "+Z",
        "license": "Model tubuh, mata, alis, dan rambut: Quaternius 'Universal Base Characters' (Standard), CC0 1.0 (lihat THIRD_PARTY_ASSETS.md). Pakaian & animasi: dibuat SILATARA.",
        "costume": "Baju & celana latihan generik (hijau tua) dan sabuk polos. Tanpa emblem atau warna tingkatan perguruan.",
        "not_a_mascot": True, "source_pipeline": ["tools/character/build_quaternius.py", "tools/character/animate.py"],
        "blender": "Tidak dipakai. Retarget dan perakitan dilakukan oleh skrip Python di repositori ini.",
        "third_party": {"name": "Universal Base Characters [Standard]", "author": "Quaternius", "license": "CC0 1.0", "url": "https://quaternius.com/packs/universalbasecharacters.html"},
    }
    (out / "character.json").write_text(json.dumps(character, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "clips.json").write_text(json.dumps({"schema": "silatara.character-clips/v1", "character_version": VERSION, "clips": clips_meta}, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {"clips": len(report), "ok": sum(1 for r in report if r["ok"]), "glb_bytes": size, "build_seconds": round(time.time() - t0, 1)}
    (out / "validation.json").write_text(json.dumps({"clips": report, "character_version": VERSION, "generated_at": time.strftime("%Y-%m-%d"), "summary": summary,
                                                      "method": "retarget rotasi delta dunia + IK tungkai; validasi pada rig target"}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary))
    return 0 if summary["ok"] == summary["clips"] else 1


if __name__ == "__main__":
    sys.exit(main())
