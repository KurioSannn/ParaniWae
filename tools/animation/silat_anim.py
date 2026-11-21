"""Generator animasi vektor SILATARA (hanya stdlib Python).

Masukan : rig.json (bersama) + keyframes.json per gerakan.
Keluaran: animation.svg (SMIL, loop, tanpa JavaScript/URL eksternal), thumbnail.svg (pose awal statis),
          rig.json (salinan rig yang dipakai), animation-manifest.json.

Model: segmen kaku bersarang (pelvis -> torso -> lengan; pelvis -> paha -> tulang kering -> telapak) dengan pivot sendi.
Sudut kaki dihitung dengan IK dua-ruas per frame sehingga pergelangan kaki tepat di target (telapak tidak
"melayang"/tergelincir). Timeline pose diinterpolasi (smoothstep) lalu disampel rapat; nilai sudut ditulis ke
<animateTransform type="rotate"> sehingga browser tidak perlu skrip.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

GENERATOR_VERSION = "1.0.0"
FPS = 20
IK_TOLERANCE_PX = 0.75


class AnimationError(ValueError):
    pass


# ---------------------------------------------------------------- geometri dasar
def rot(theta_deg: float, v: tuple[float, float]) -> tuple[float, float]:
    """Rotasi SVG (searah jarum jam positif, sumbu y ke bawah)."""
    t = math.radians(theta_deg)
    c, s = math.cos(t), math.sin(t)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def theta_of_down_segment(vec: tuple[float, float]) -> float:
    """Sudut rotasi SVG yang memutar vektor (0,1) menjadi arah `vec`."""
    return -math.degrees(math.atan2(vec[0], vec[1]))


def smoothstep(u: float) -> float:
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * u
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [lerp(x, y, u) for x, y in zip(a, b, strict=True)]
    if isinstance(a, dict) and isinstance(b, dict):
        return {k: lerp(a[k], b[k], u) if k in b else a[k] for k in a}
    return a if u < 0.5 else b  # kategorikal (bentuk tangan)


# ---------------------------------------------------------------- pose
DEFAULT_POSE = {
    "pelvis": [180, 0],
    "torso": 0,
    "head": 0,
    "gaze": 0,
    "feet": {"L": [188, 0], "R": [172, 0]},
    "arms": {"L": [8, 0], "R": [8, 0]},
    "hands": {"L": "open", "R": "open"},
    "foot_pitch": {"L": 0, "R": 0},
    "foot_turn": {"L": 20, "R": 20},
}


def full_pose(p: dict) -> dict:
    out = copy.deepcopy(DEFAULT_POSE)
    for k, v in p.items():
        if k in ("feet", "arms", "hands", "foot_pitch", "foot_turn") and isinstance(v, dict):
            out[k].update(v)
        elif k in DEFAULT_POSE:
            out[k] = v
    return out


@dataclass
class Frame:
    t_ms: float
    pose: dict
    theta: dict = field(default_factory=dict)  # sudut dunia per segmen
    points: dict = field(default_factory=dict)  # posisi sendi dunia
    ik_error: float = 0.0


def solve(rig: dict, view: str, pose: dict) -> Frame:
    seg, cv = rig["segments"], rig["canvas"]
    off = rig["offsets"][view]
    ground = cv["ground_y"]
    leg = seg["thigh"] + seg["shin"]
    stand_y = ground - seg["ankle_h"] - leg * 0.995
    px, drop = pose["pelvis"]
    P = (px, stand_y + drop)
    f = Frame(0.0, pose)
    th, pts = f.theta, f.points
    pts["pelvis"] = P

    # --- kaki (IK dua-ruas)
    for side in ("L", "R"):
        sgn = (1 if side == "L" else -1) if view == "front" else 0
        H = (P[0] + sgn * off["hip"], P[1])
        fx, lift = pose["feet"][side]
        A = (fx, ground - seg["ankle_h"] - lift)
        L1, L2 = seg["thigh"], seg["shin"]
        dx, dy = A[0] - H[0], A[1] - H[1]
        d = math.hypot(dx, dy)
        err = 0.0
        if d > L1 + L2:
            err = d - (L1 + L2)
            d = L1 + L2 - 1e-6
        if d < abs(L1 - L2) + 1e-6:
            err = max(err, abs(L1 - L2) - d)
            d = abs(L1 - L2) + 1e-3
        f.ik_error = max(f.ik_error, err)
        base = math.atan2(dy, dx)
        alpha = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
        cands = [
            (H[0] + L1 * math.cos(base + alpha), H[1] + L1 * math.sin(base + alpha)),
            (H[0] + L1 * math.cos(base - alpha), H[1] + L1 * math.sin(base - alpha)),
        ]
        if view == "side":
            K = max(cands, key=lambda k: k[0])  # lutut menekuk ke depan (+x)
        else:
            K = max(cands, key=lambda k: k[0]) if side == "L" else min(cands, key=lambda k: k[0])
        # posisi pergelangan sebenarnya (setelah clamp) mengikuti arah target
        ux, uy = (dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)) if (dx or dy) else (0.0, 1.0)
        A_real = (H[0] + ux * d, H[1] + uy * d) if err else A
        # koreksi kecil: hitung ulang K terhadap A_real bila di-clamp
        th[f"thigh.{side}"] = theta_of_down_segment((K[0] - H[0], K[1] - H[1]))
        th[f"shin.{side}"] = theta_of_down_segment((A_real[0] - K[0], A_real[1] - K[1]))
        pitch = pose["foot_pitch"][side] if view == "side" else 0
        turn = pose["foot_turn"][side] if view == "front" else 0
        th[f"foot.{side}"] = pitch if view == "side" else (-turn if side == "L" else turn) * 0.5
        pts[f"hip.{side}"], pts[f"knee.{side}"], pts[f"ankle.{side}"] = H, K, A_real
        if view == "side":
            toe = add(A_real, rot(pitch, (seg["foot_len"], seg["ankle_h"])))
            heel = add(A_real, rot(pitch, (-8, seg["ankle_h"])))
            pts[f"toe.{side}"], pts[f"heel.{side}"] = toe, heel
        else:
            pts[f"toe.{side}"] = (A_real[0], A_real[1] + seg["ankle_h"])

    # --- torso, kepala
    tt = pose["torso"]
    th["torso"] = tt
    N = add(P, rot(tt, (0, -seg["torso"])))
    pts["neck"] = N
    th["head"] = tt + pose["head"]
    head_c = add(N, rot(th["head"], (0, -(seg["neck"] + seg["head_r"]))))
    pts["head"] = head_c
    pts["head_top"] = add(head_c, (0, -seg["head_r"]))

    # --- lengan
    for side in ("L", "R"):
        a_sh, a_el = pose["arms"][side]
        if view == "front":
            sx = off["shoulder"] if side == "L" else -off["shoulder"]
            S = add(P, rot(tt, (sx, -seg["torso"] + off["shoulder_drop"])))
            t_ua = tt - a_sh if side == "L" else tt + a_sh
            t_fa = t_ua + a_el if side == "L" else t_ua - a_el
        else:
            S = add(P, rot(tt, (0, -seg["torso"] + off["shoulder_drop"])))
            t_ua = tt - a_sh
            t_fa = t_ua - a_el
        E = add(S, rot(t_ua, (0, seg["upper_arm"])))
        W = add(E, rot(t_fa, (0, seg["forearm"])))
        Hc = add(W, rot(t_fa, (0, seg["hand_r"] * 0.8)))
        th[f"upper_arm.{side}"], th[f"forearm.{side}"] = t_ua, t_fa
        pts[f"shoulder.{side}"], pts[f"elbow.{side}"], pts[f"wrist.{side}"], pts[f"hand.{side}"] = S, E, W, Hc
    return f


# ---------------------------------------------------------------- timeline
def expand_timeline(spec: dict) -> tuple[list[tuple], float]:
    poses = {k["id"]: k for k in spec["keyframes"]}
    seq = spec["sequence"]
    if not seq:
        raise AnimationError("sequence kosong")
    segs, t = [], 0.0
    prev = None
    for i, step in enumerate(seq):
        kf = poses.get(step["pose"])
        if kf is None:
            raise AnimationError(f"sequence[{i}] menunjuk pose tak dikenal {step['pose']}")
        move = float(step.get("move_ms", 0))
        hold = float(step.get("hold_ms", 0))
        if prev is not None and move > 0:
            segs.append((t, t + move, prev, kf, "move"))
            t += move
        elif prev is not None and move <= 0:
            raise AnimationError(f"sequence[{i}] butuh move_ms > 0")
        if hold > 0:
            segs.append((t, t + hold, kf, kf, "hold"))
            t += hold
        prev = kf
    ret = float(spec.get("return_ms", 0))
    first = poses[seq[0]["pose"]]
    if ret > 0 and prev is not first:
        segs.append((t, t + ret, prev, first, "move"))
        t += ret
    elif prev is not first and ret <= 0:
        raise AnimationError("return_ms wajib > 0 agar loop kembali ke pose awal tanpa lompatan")
    return segs, t


def pose_at(segs, t: float) -> tuple[dict, str]:
    for a, b, k0, k1, kind in segs:
        if t <= b + 1e-9:
            u = 0.0 if b == a else (t - a) / (b - a)
            if kind == "hold":
                return full_pose(k0["pose"]), k0["id"]
            return lerp(full_pose(k0["pose"]), full_pose(k1["pose"]), smoothstep(u)), (k1["id"] if u >= 0.5 else k0["id"])
    last = segs[-1]
    return full_pose(last[3]["pose"]), last[3]["id"]


def sample(rig, spec) -> tuple[list[Frame], float, list]:
    segs, total = expand_timeline(spec)
    n = max(2, round(total / 1000 * FPS))
    frames = []
    for i in range(n + 1):
        t = total * i / n
        pose, _ = pose_at(segs, t)
        fr = solve(rig, spec["view"], pose)
        fr.t_ms = t
        frames.append(fr)
    return frames, total, segs


def phase_windows(segs, total) -> dict[str, list[float]]:
    """Rentang waktu (0..1) tiap keyframe: dari tengah transisi masuk sampai tengah transisi keluar."""
    win: dict[str, list[float]] = {}
    marks = []  # (t_switch, kf_id)
    for a, b, k0, k1, kind in segs:
        if kind == "hold":
            marks.append((a, k0["id"]))
        else:
            marks.append(((a + b) / 2, k1["id"]))
    marks.sort()
    cur_id, cur_t = segs[0][2]["id"], 0.0
    spans = []
    for t, kid in marks:
        if kid != cur_id:
            spans.append((cur_id, cur_t, t))
            cur_id, cur_t = kid, t
    spans.append((cur_id, cur_t, total))
    for kid, a, b in spans:
        if b - a > 1e-6:
            win.setdefault(kid, []).append(round(a / total, 4))
            win[kid].append(round(b / total, 4))
    return win


# ---------------------------------------------------------------- SVG
def _f(x: float) -> str:
    s = f"{x:.1f}"
    return "0" if s in ("-0.0", "0.0") else s.rstrip("0").rstrip(".") if "." in s else s


def _rotate_anim(values: list[float], dur: float, static: bool) -> str:
    if static:
        return ""
    return (
        f'<animateTransform attributeName="transform" type="rotate" dur="{dur / 1000:.3f}s" '
        f'repeatCount="indefinite" calcMode="linear" values="{";".join(_f(v) for v in values)}"/>'
    )


def _discrete_opacity(windows: list[float], dur: float, static: bool, visible_at0: bool) -> str:
    """windows: [a0,b0,a1,b1,...] (0..1) saat terlihat."""
    if static:
        return ""
    pts = [(0.0, 0)]
    for i in range(0, len(windows), 2):
        pts.append((windows[i], 1))
        pts.append((windows[i + 1], 0))
    pts.sort()
    merged: dict[float, int] = {}
    for t, v in pts:
        merged[round(t, 4)] = v
    keys = sorted(k for k in merged if k < 1.0)
    vals = [merged[k] for k in keys]
    # buang duplikat berurutan
    kt, vv = [], []
    for k, v in zip(keys, vals, strict=True):
        if vv and vv[-1] == v:
            continue
        kt.append(k)
        vv.append(v)
    if kt[0] != 0.0:
        kt.insert(0, 0.0)
        vv.insert(0, 0)
    return (
        f'<animate attributeName="opacity" dur="{dur / 1000:.3f}s" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{";".join(f"{k:g}" for k in kt)}" values="{";".join(str(v) for v in vv)}"/>'
    )


def _limb_shapes(rig, kind: str, far: bool) -> str:
    seg, pal = rig["segments"], rig["palette"]
    cloth = pal["cloth_far"] if far else pal["cloth"]
    if kind == "thigh":
        L = seg["thigh"]
        return f'<path d="M-11,-4 L11,-4 L9,{L} L-9,{L} Z" fill="{cloth}" stroke="{pal["outline"]}" stroke-width="2" stroke-linejoin="round"/>'
    if kind == "shin":
        L = seg["shin"]
        return (
            f'<path d="M-9,-2 L9,-2 L6.5,{L - 6} L-6.5,{L - 6} Z" fill="{cloth}" stroke="{pal["outline"]}" stroke-width="2" stroke-linejoin="round"/>'
            f'<rect x="-6.5" y="{L - 9}" width="13" height="9" rx="3" fill="{pal["skin_far"] if far else pal["skin"]}" stroke="{pal["outline"]}" stroke-width="1.5"/>'
        )
    if kind == "upper_arm":
        L = seg["upper_arm"]
        return f'<rect x="-7.5" y="-6" width="15" height="{L + 10}" rx="7.5" fill="{cloth}" stroke="{pal["outline"]}" stroke-width="2"/>'
    if kind == "forearm":
        L = seg["forearm"]
        return f'<rect x="-6.5" y="-6" width="13" height="{L + 8}" rx="6.5" fill="{cloth}" stroke="{pal["outline"]}" stroke-width="2"/>'
    raise AnimationError(kind)


def _foot_shape(rig, view, far):
    seg, pal = rig["segments"], rig["palette"]
    skin = pal["skin_far"] if far else pal["skin"]
    if view == "side":
        fl, ah = seg["foot_len"], seg["ankle_h"]
        return f'<path d="M-9,-2 Q-11,{ah} -6,{ah} L{fl},{ah} Q{fl + 3},{ah - 5} {fl - 6},{ah - 7} L4,-3 Z" fill="{skin}" stroke="{pal["outline"]}" stroke-width="1.8" stroke-linejoin="round"/>'
    return f'<path d="M-7,-2 L7,-2 L9,{seg["ankle_h"]} L-9,{seg["ankle_h"]} Z" fill="{skin}" stroke="{pal["outline"]}" stroke-width="1.8" stroke-linejoin="round"/>'


def _hand_shapes(rig, kid, side, far, frames, dur, static):
    pal, seg = rig["palette"], rig["segments"]
    skin = pal["skin_far"] if far else pal["skin"]
    r = seg["hand_r"]
    states = [fr.pose["hands"][side] for fr in frames]
    out = []
    for shape in ("fist", "open"):
        win, inside, start = [], False, 0.0
        n = max(1, len(states) - 1)
        for i, s in enumerate(states):
            on = (s == shape) or (shape == "open" and s not in ("fist", "open"))
            if on and not inside:
                inside, start = True, i / n
            if not on and inside:
                inside = False
                win += [start, i / n]
        if inside:
            win += [start, 1.0]
        if not win:
            continue
        if shape == "fist":
            g = f'<circle cx="0" cy="{r * 0.7}" r="{r}" fill="{skin}" stroke="{pal["outline"]}" stroke-width="1.8"/><path d="M-4,{r * 0.5} h8" stroke="{pal["outline"]}" stroke-width="1.2"/>'
        else:
            g = f'<rect x="-{r * 0.75}" y="-2" width="{r * 1.5}" height="{r * 2.4}" rx="{r * 0.7}" fill="{skin}" stroke="{pal["outline"]}" stroke-width="1.8"/>'
        full = win == [0.0, 1.0]
        op = "" if full else _discrete_opacity(win, dur, static, states[0] == shape)
        init = "1" if (states[0] == shape or (shape == "open" and states[0] not in ("fist", "open"))) else "0"
        out.append(f'<g id="{kid}-hand-{side}-{shape}" opacity="{init}">{op}{g}</g>')
    return "".join(out)


def render_figure_svg(rig, spec, frames, total, segs, *, static=False) -> tuple[str, dict]:
    view = spec["view"]
    if view not in ("front", "side"):
        raise AnimationError(f"view tidak dikenal: {view}")
    seg, pal, cv, off = rig["segments"], rig["palette"], rig["canvas"], rig["offsets"][view]
    aid = spec["animation_id"]
    W, H = cv["width"], cv["height"]
    dur = total
    fr_used = frames[:1] if static else frames

    def vals(key):
        return [fr.theta[key] for fr in fr_used]

    def rel(child, parent):
        return [fr.theta[child] - (fr.theta[parent] if parent else 0.0) for fr in fr_used]

    def g_rot(values, inner, gid=None):
        idattr = f' id="{gid}"' if gid else ""
        if static:
            return f'<g{idattr} transform="rotate({_f(values[0])})">{inner}</g>'
        return f'<g{idattr}>{_rotate_anim(values, dur, False)}{inner}</g>'

    def leg(side, far):
        hx = (off["hip"] if side == "L" else -off["hip"]) if view == "front" else 0
        foot = g_rot(rel(f"foot.{side}", f"shin.{side}"), _foot_shape(rig, view, far), f"{aid}-foot-{side}")
        shin = g_rot(
            rel(f"shin.{side}", f"thigh.{side}"),
            _limb_shapes(rig, "shin", far) + f'<g transform="translate(0,{seg["shin"]})">{foot}</g>',
            f"{aid}-shin-{side}",
        )
        thigh = g_rot(
            vals(f"thigh.{side}"),
            _limb_shapes(rig, "thigh", far) + f'<g transform="translate(0,{seg["thigh"]})">{shin}</g>',
            f"{aid}-thigh-{side}",
        )
        return f'<g transform="translate({_f(hx)},0)">{thigh}</g>'

    def arm(side, far):
        if view == "front":
            sx = off["shoulder"] if side == "L" else -off["shoulder"]
        else:
            sx = 0
        sy = -seg["torso"] + off["shoulder_drop"]
        hands = _hand_shapes(rig, aid, side, far, fr_used, dur, static)
        fore = g_rot(
            rel(f"forearm.{side}", f"upper_arm.{side}"),
            _limb_shapes(rig, "forearm", far) + f'<g transform="translate(0,{seg["forearm"]})">{hands}</g>',
            f"{aid}-forearm-{side}",
        )
        upper = g_rot(
            rel(f"upper_arm.{side}", "torso"),
            _limb_shapes(rig, "upper_arm", far) + f'<g transform="translate(0,{seg["upper_arm"]})">{fore}</g>',
            f"{aid}-upperarm-{side}",
        )
        return f'<g transform="translate({_f(sx)},{_f(sy)})">{upper}</g>'

    # kepala
    hr = seg["head_r"]
    if view == "side":
        face = f'<path d="M{hr - 2},-4 L{hr + 5},2 L{hr - 1},5 Z" fill="{pal["skin"]}" stroke="{pal["outline"]}" stroke-width="1.5" stroke-linejoin="round"/>'
        eyes = f'<circle cx="{hr * 0.45}" cy="-3" r="2.2" fill="{pal["outline"]}"/>'
    else:
        gz = [fr.pose["gaze"] * 7 for fr in fr_used]
        if static:
            eyes = f'<g transform="translate({_f(gz[0])},0)"><circle cx="-7" cy="-2" r="2.2" fill="{pal["outline"]}"/><circle cx="7" cy="-2" r="2.2" fill="{pal["outline"]}"/></g>'
        else:
            eyes = (
                f'<g><animateTransform attributeName="transform" type="translate" dur="{dur / 1000:.3f}s" repeatCount="indefinite" '
                f'values="{";".join(_f(v) + ",0" for v in gz)}"/><circle cx="-7" cy="-2" r="2.2" fill="{pal["outline"]}"/><circle cx="7" cy="-2" r="2.2" fill="{pal["outline"]}"/></g>'
            )
        face = ""
    head_inner = (
        f'<rect x="-5" y="-{seg["neck"] + 2}" width="10" height="{seg["neck"] + 4}" fill="{pal["skin"]}" stroke="{pal["outline"]}" stroke-width="1.5"/>'
        f'<g transform="translate(0,-{seg["neck"] + hr})"><circle r="{hr}" fill="{pal["skin"]}" stroke="{pal["outline"]}" stroke-width="2"/>'
        f'<path d="M-{hr - 0.5},-4 A{hr},{hr} 0 0 1 {hr - 0.5},-4 Q0,-{hr * 0.55} -{hr - 0.5},-4 Z" fill="{pal["outline"]}" opacity="0.9"/>'
        f"{face}{eyes}</g>"
    )
    T = seg["torso"]
    head = f'<g transform="translate(0,-{T})">' + g_rot(rel("head", "torso"), head_inner, f"{aid}-head") + "</g>"
    tw = 2 * off["shoulder"] + 8 if view == "front" else 30
    pw = 2 * off["hip"] + 18 if view == "front" else 30
    torso_shape = (
        f'<path d="M-{pw / 2},6 L{pw / 2},6 L{tw / 2},-{T - 4} Q{tw / 2},-{T + 2} {tw / 2 - 8},-{T + 2} '
        f'L-{tw / 2 - 8},-{T + 2} Q-{tw / 2},-{T + 2} -{tw / 2},-{T - 4} Z" fill="{pal["cloth"]}" stroke="{pal["outline"]}" stroke-width="2" stroke-linejoin="round"/>'
        f'<rect x="-{pw / 2 + 1}" y="-8" width="{pw + 2}" height="11" rx="3" fill="{pal["sash"]}" stroke="{pal["outline"]}" stroke-width="1.5"/>'
    )
    if view == "side":
        torso_inner = arm("R", True) + torso_shape + head + arm("L", False)
        legs = leg("R", True) + leg("L", False)
    else:
        order = spec.get("leg_order", ["L", "R"])  # yang terakhir digambar di depan
        torso_inner = torso_shape + head + arm("R", False) + arm("L", False)
        legs = "".join(leg(s, False) for s in order)
    torso = g_rot(vals("torso"), torso_inner, f"{aid}-torso")
    pel = f'<path d="M-{pw / 2},-6 L{pw / 2},-6 L{pw / 2 - 2},10 L-{pw / 2 - 2},10 Z" fill="{pal["cloth"]}" stroke="{pal["outline"]}" stroke-width="2"/>'
    if static:
        p0 = fr_used[0].points["pelvis"]
        root = f'<g id="{aid}-root" transform="translate({_f(p0[0])},{_f(p0[1])})">{legs}{pel}{torso}</g>'
    else:
        tv = ";".join(f'{_f(fr.points["pelvis"][0])},{_f(fr.points["pelvis"][1])}' for fr in fr_used)
        root = (
            f'<g id="{aid}-root"><animateTransform attributeName="transform" type="translate" dur="{dur / 1000:.3f}s" '
            f'repeatCount="indefinite" values="{tv}"/>{legs}{pel}{torso}</g>'
        )

    # bayangan & lantai
    gy = cv["ground_y"]
    if static:
        shadow = f'<ellipse cx="{_f(fr_used[0].points["pelvis"][0])}" cy="{gy + 4}" rx="58" ry="6" fill="{pal["ground"]}"/>'
    else:
        sx = ";".join(_f(fr.points["pelvis"][0]) for fr in fr_used)
        shadow = f'<ellipse cy="{gy + 4}" rx="58" ry="6" fill="{pal["ground"]}"><animate attributeName="cx" dur="{dur / 1000:.3f}s" repeatCount="indefinite" values="{sx}"/></ellipse>'

    captions = _captions(spec, segs, total, static, pal, W)
    arrows = _arrows(spec, segs, total, static, pal)
    title = escape(spec["title"])
    desc = escape(spec["description"])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" id="{aid}{"-thumb" if static else ""}" '
        f'role="img" aria-labelledby="{aid}-title {aid}-desc" data-movement-id="{spec["movement_id"]}" data-generator="silat_anim {GENERATOR_VERSION}">'
        f'<title id="{aid}-title">{title}</title><desc id="{aid}-desc">{desc}</desc>'
        f'<rect width="{W}" height="{H}" fill="{pal["background"]}"/>'
        f'<line x1="12" y1="{gy + 4}" x2="{W - 12}" y2="{gy + 4}" stroke="{pal["ground"]}" stroke-width="3" stroke-linecap="round"/>'
        f"{shadow}{arrows}<g id=\"{aid}-figure\">{root}</g>{captions}"
        f'<text x="{W - 10}" y="{H - 8}" text-anchor="end" font-family="system-ui,sans-serif" font-size="9" fill="{pal["caption_muted"]}">'
        f"Ilustrasi gerak SILATARA · tampak {'depan' if view == 'front' else 'samping'}</text>"
        "</svg>"
    )
    return svg, {"phase_windows": phase_windows(segs, total)}


def _captions(spec, segs, total, static, pal, W):
    win = phase_windows(segs, total)
    out = []
    first = spec["sequence"][0]["pose"]
    for kf in spec["keyframes"]:
        if kf["id"] not in win:
            continue
        w = win[kf["id"]]
        if static and kf["id"] != first:
            continue
        op = "" if static or w == [0.0, 1.0] else _discrete_opacity(w, total, False, kf["id"] == first)
        init = "1" if kf["id"] == first else "0"
        out.append(
            f'<g id="{spec["animation_id"]}-cap-{kf["id"]}" opacity="{init}">{op}'
            f'<text x="{W / 2}" y="28" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="600" fill="{pal["caption"]}">{escape(kf["label"])}</text>'
            + (
                f'<text x="{W / 2}" y="46" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" fill="{pal["caption_muted"]}">{escape(kf["caption"])}</text>'
                if kf.get("caption")
                else ""
            )
            + "</g>"
        )
    return "".join(out)


def _arrows(spec, segs, total, static, pal):
    win = phase_windows(segs, total)
    out = []
    for kf in spec["keyframes"]:
        a = kf.get("arrow")
        if not a or kf["id"] not in win:
            continue
        (x1, y1), (x2, y2) = a["from"], a["to"]
        ang = math.atan2(y2 - y1, x2 - x1)
        hx1, hy1 = x2 - 9 * math.cos(ang - 0.45), y2 - 9 * math.sin(ang - 0.45)
        hx2, hy2 = x2 - 9 * math.cos(ang + 0.45), y2 - 9 * math.sin(ang + 0.45)
        op = "" if static else _discrete_opacity(win[kf["id"]], total, False, False)
        init = "0" if not static else "1"
        if static and kf["id"] != spec["sequence"][0]["pose"]:
            continue
        out.append(
            f'<g id="{spec["animation_id"]}-arrow-{kf["id"]}" opacity="{init}">{op}'
            f'<path d="M{_f(x1)},{_f(y1)} L{_f(x2)},{_f(y2)} M{_f(hx1)},{_f(hy1)} L{_f(x2)},{_f(y2)} L{_f(hx2)},{_f(hy2)}" '
            f'stroke="{pal["accent"]}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>'
        )
    return "".join(out)


# ---------------------------------------------------------------- tampilan atas (diagram langkah)
def render_top_svg(rig, spec, *, static=False) -> tuple[str, dict, float]:
    pal, cv = rig["palette"], rig["canvas"]
    W, H = cv["width"], cv["height"]
    aid = spec["animation_id"]
    marks = spec["markers"]
    step_ms, hold_ms = float(spec.get("step_ms", 700)), float(spec.get("end_hold_ms", 1200))
    total = step_ms * len(marks) + hold_ms
    dur = f"{total / 1000:.3f}s"
    parts = [f'<rect width="{W}" height="{H}" fill="{pal["background"]}"/>']
    for g in spec.get("guides", []):
        if g["type"] == "line":
            (x1, y1), (x2, y2) = g["from"], g["to"]
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{pal["ground"]}" stroke-width="{g.get("w", 2)}" stroke-dasharray="{g.get("dash", "0")}"/>')
        elif g["type"] == "label":
            parts.append(f'<text x="{g["at"][0]}" y="{g["at"][1]}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="{g.get("size", 11)}" fill="{pal["caption_muted"]}">{escape(g["text"])}</text>')
        elif g["type"] == "circle":
            parts.append(f'<circle cx="{g["at"][0]}" cy="{g["at"][1]}" r="{g["r"]}" fill="none" stroke="{pal["ground"]}" stroke-width="2"/>')
    win: dict[str, list[float]] = {}
    for i, m in enumerate(marks):
        t_on = (i * step_ms) / total
        win[m["id"]] = [round(t_on, 4), 1.0]
        x, y = m["pos"]
        foot = m.get("foot")
        fill = pal["cloth"] if foot == "L" else (pal["sash"] if foot == "R" else pal["cloth_far"])
        shape = (
            f'<ellipse cx="{x}" cy="{y}" rx="9" ry="14" fill="{fill}" stroke="{pal["outline"]}" stroke-width="1.5" transform="rotate({m.get("rot", 0)} {x} {y})"/>'
            if foot
            else f'<circle cx="{x}" cy="{y}" r="11" fill="{fill}" stroke="{pal["outline"]}" stroke-width="1.5"/>'
        )
        lbl = f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" font-weight="700" fill="#FCFBF7">{escape(m["label"])}</text>'
        if static:
            parts.append(f'<g id="{aid}-mk-{m["id"]}" opacity="{1 if i == 0 else 0.25}">{shape}{lbl}</g>')
        else:
            parts.append(
                f'<g id="{aid}-mk-{m["id"]}" opacity="0.18"><animate attributeName="opacity" dur="{dur}" repeatCount="indefinite" calcMode="discrete" '
                f'keyTimes="0;{t_on:.4f}" values="0.18;1"/>{shape}{lbl}</g>'
            )
    # penanda aktif bergerak
    xs = [m["pos"] for m in marks]
    if static:
        parts.append(f'<circle cx="{xs[0][0]}" cy="{xs[0][1]}" r="17" fill="none" stroke="{pal["accent"]}" stroke-width="3"/>')
    else:
        vals = []
        kts = []
        for i, p in enumerate(xs):
            t0 = i * step_ms / total
            vals.append(f"{p[0]},{p[1]}")
            kts.append(f"{t0:.4f}")
        vals.append(f"{xs[-1][0]},{xs[-1][1]}")
        kts.append("1")
        parts.append(
            f'<circle r="17" fill="none" stroke="{pal["accent"]}" stroke-width="3"><animateTransform attributeName="transform" type="translate" dur="{dur}" '
            f'repeatCount="indefinite" calcMode="discrete" keyTimes="{";".join(kts)}" values="{";".join(vals)}"/></circle>'
        )
    cap = escape(spec.get("legend", ""))
    parts.append(f'<text x="{W / 2}" y="26" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="600" fill="{pal["caption"]}">{escape(spec["title"])}</text>')
    if cap:
        parts.append(f'<text x="{W / 2}" y="{H - 24}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="10" fill="{pal["caption_muted"]}">{cap}</text>')
    parts.append(f'<text x="{W - 10}" y="{H - 8}" text-anchor="end" font-family="system-ui,sans-serif" font-size="9" fill="{pal["caption_muted"]}">Diagram langkah SILATARA · tampak atas</text>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" id="{aid}{"-thumb" if static else ""}" role="img" '
        f'aria-labelledby="{aid}-title {aid}-desc" data-movement-id="{spec["movement_id"]}" data-generator="silat_anim {GENERATOR_VERSION}">'
        f'<title id="{aid}-title">{escape(spec["title"])}</title><desc id="{aid}-desc">{escape(spec["description"])}</desc>'
        + "".join(parts)
        + "</svg>"
    )
    return svg, {"phase_windows": win}, total


# ---------------------------------------------------------------- bounds
def frame_bounds(rig, frames) -> tuple[float, float, float, float]:
    xs, ys = [], []
    hr, hand = rig["segments"]["head_r"], rig["segments"]["hand_r"]
    for fr in frames:
        for k, (x, y) in fr.points.items():
            pad = hr if k == "head" else (hand + 2 if k.startswith("hand") else 12)
            xs += [x - pad, x + pad]
            ys += [y - pad, y + pad]
    return min(xs), min(ys), max(xs), max(ys)


# ---------------------------------------------------------------- build
def build(anim_dir: Path, rig_path: Path) -> dict:
    rig = json.loads(rig_path.read_text())
    spec = json.loads((anim_dir / "keyframes.json").read_text())
    if spec.get("animation_status") != "generated":
        raise AnimationError(f"{anim_dir.name}: animation_status bukan 'generated'")
    view = spec["view"]
    if view == "top":
        svg, meta, total = render_top_svg(rig, spec)
        thumb, _, _ = render_top_svg(rig, spec, static=True)
        bounds = None
        frames_n, ik = 0, 0.0
    else:
        frames, total, segs = sample(rig, spec)
        svg, meta = render_figure_svg(rig, spec, frames, total, segs)
        thumb, _ = render_figure_svg(rig, spec, frames, total, segs, static=True)
        bounds = frame_bounds(rig, frames)
        frames_n = len(frames)
        ik = max(fr.ik_error for fr in frames)
        if ik > IK_TOLERANCE_PX:
            raise AnimationError(f"{anim_dir.name}: pose tidak terjangkau kaki (galat IK {ik:.2f}px)")
    (anim_dir / "animation.svg").write_text(svg)
    (anim_dir / "thumbnail.svg").write_text(thumb)
    rig_copy = dict(rig)
    rig_copy["_copied_from"] = "tools/animation/rig.json"
    (anim_dir / "rig.json").write_text(json.dumps(rig_copy, indent=2, ensure_ascii=False) + "\n")
    manifest = {
        "schema": "silatara.animation-manifest/v1",
        "animation_id": spec["animation_id"],
        "movement_id": spec["movement_id"],
        "animation_status": "generated",
        "view": view,
        "duration_ms": round(total),
        "loop": True,
        "fps_sampled": FPS if view != "top" else None,
        "frames": frames_n,
        "playback_rates": [0.5, 1.0, 1.5],
        "playback_note": "SMIL tidak memiliki kontrol kecepatan bawaan; pemutar dapat memakai SVGSVGElement.pauseAnimations()/setCurrentTime() atau merender ulang dengan dur berbeda.",
        "phase_map": {
            kf["id"]: {"phase_id": kf.get("phase_id"), "label": kf.get("label"), "windows": meta["phase_windows"].get(kf["id"], [])}
            for kf in spec.get("keyframes", spec.get("markers", []))
        },
        "bounds": [round(b, 1) for b in bounds] if bounds else None,
        "max_ik_error_px": round(ik, 3),
        "rig_id": rig["rig_id"],
        "rig_version": rig["version"],
        "generator": f"tools/animation/silat_anim.py {GENERATOR_VERSION}",
        "keyframes_sha256": hashlib.sha256((anim_dir / "keyframes.json").read_bytes()).hexdigest(),
        "svg_sha256": hashlib.sha256(svg.encode()).hexdigest(),
        "svg_bytes": len(svg.encode()),
        "source_ids": spec.get("source_ids", []),
        "authorship": "Interpretasi visual editorial tim SILATARA atas dokumentasi tertulis; bukan rekaman manusia; bukan demonstrasi resmi perguruan.",
        "instructor_validation": "not_validated",
    }
    (anim_dir / "animation-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest
