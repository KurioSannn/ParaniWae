"""Bangun research/pencak-silat/directory/regions.json dari dataset kode wilayah Kepmendagri (cahyadsn/wilayah, MIT).

Hanya pustaka standar. Masukan: berkas SQL `wilayah_level_1_2.sql` (provinsi + kabupaten/kota, titik ibu kota,
poligon batas). Poligon disederhanakan (Douglas-Peucker, toleransi ~0,005°) untuk uji titik-dalam-poligon;
bukan untuk ditampilkan sebagai batas resmi.

Pemakaian: python tools/directory/build_regions.py <wilayah_level_1_2.sql> <out.json>
"""
from __future__ import annotations

import json
import sys

TOL = 0.005


def tokenize_values(s: str, start: int):
    """Urai satu tuple SQL mulai dari '(' pada `start`. Kembalikan (nilai[], posisi setelah ')')."""
    assert s[start] == "("
    i, vals, n = start + 1, [], len(s)
    while i < n:
        c = s[i]
        if c in " \n\t,":
            i += 1
            continue
        if c == ")":
            return vals, i + 1
        if c == "'":
            j, buf = i + 1, []
            while True:
                if s[j] == "\\":
                    buf.append(s[j + 1]); j += 2; continue
                if s[j] == "'":
                    if j + 1 < n and s[j + 1] == "'":
                        buf.append("'"); j += 2; continue
                    break
                buf.append(s[j]); j += 1
            vals.append("".join(buf)); i = j + 1
            continue
        j = i
        while s[j] not in ",)":
            j += 1
        tok = s[i:j].strip()
        vals.append(None if tok.upper() == "NULL" else float(tok))
        i = j
    raise ValueError("tuple tak tertutup")


def rdp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    norm = (dx * dx + dy * dy) ** 0.5 or 1e-12
    dmax, idx = 0.0, 0
    for k in range(1, len(pts) - 1):
        p = pts[k]
        d = abs(dy * (p[0] - a[0]) - dx * (p[1] - a[1])) / norm
        if d > dmax:
            dmax, idx = d, k
    if dmax > tol:
        return rdp(pts[: idx + 1], tol)[:-1] + rdp(pts[idx:], tol)
    return [a, b]


def rings_of(path):
    """Normalisasi ke daftar ring [[lat,lng],...]. Dataset memakai [[[lat,lng],...], ...] (bisa bersarang lebih)."""
    out = []

    def walk(x):
        if isinstance(x, list) and x and isinstance(x[0], (int, float)):
            return
        if isinstance(x, list) and x and isinstance(x[0], list) and x[0] and isinstance(x[0][0], (int, float)):
            out.append(x)
            return
        for y in x:
            walk(y)

    walk(path)
    return out


def main(src: str, dst: str) -> None:
    s = open(src, encoding="utf-8").read()
    provinces, regencies, broken = [], [], []
    pos = 0
    while True:
        k = s.find("('", pos)
        if k < 0:
            break
        try:
            vals, pos = tokenize_values(s, k)
        except (ValueError, IndexError):
            pos = k + 2
            continue
        if len(vals) != 11:
            continue
        kode, nama, ibukota, lat, lng, _elv, _tz, luas, _pend, path, _st = vals
        rings = []
        try:
            parsed = json.loads(path) if path else []
        except json.JSONDecodeError:
            parsed = []  # poligon rusak di dataset (mis. 32.79): wilayah tetap dicatat tanpa poligon
            broken.append(kode)
        for ring in rings_of(parsed):
            pts = [[round(p[0], 4), round(p[1], 4)] for p in ring]
            # ring tertutup: pecah di titik terjauh dari titik awal agar RDP tidak runtuh
            far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
            simp = rdp(pts[: far + 1], TOL)[:-1] + rdp(pts[far:], TOL)
            if len(simp) >= 4:
                rings.append(simp)
        rec = {"code": kode, "name": nama, "capital": ibukota, "lat": lat, "lng": lng, "area_km2": luas, "rings": rings}
        if "." in kode:
            rec["province_code"] = kode.split(".")[0]
            rec["kind"] = "kota" if nama.startswith("Kota ") else "kabupaten"
            regencies.append(rec)
        else:
            rec["kind"] = "provinsi"
            provinces.append(rec)
    out = {
        "schema": "silatara.regions/v1",
        "source": {
            "title": "Kode dan Data Wilayah Administrasi Indonesia (Kepmendagri No 300.2.2-2138 Tahun 2025)",
            "dataset": "cahyadsn/wilayah — db/wilayah_level_1_2.sql",
            "url": "https://github.com/cahyadsn/wilayah",
            "license": "MIT",
            "accessed": "2026-11-21",
            "polygon_missing": broken,
            "note": "Titik lat/lng = lokasi ibu kota wilayah. Poligon disederhanakan (toleransi 0,005°) hanya untuk uji titik-dalam-wilayah.",
        },
        "provinces": sorted(provinces, key=lambda r: r["code"]),
        "regencies": sorted(regencies, key=lambda r: r["code"]),
    }
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"provinsi={len(provinces)} kabupaten/kota={len(regencies)} ring={sum(len(r['rings']) for r in provinces + regencies)}")


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    main(sys.argv[1], sys.argv[2])
