"""Penemuan kandidat tempat lewat Google Places API (New) — Text Search. Hanya pustaka standar.

Matriks: 514 kabupaten/kota x kata kunci. Setiap kueri dibatasi ke kotak wilayah (locationRestriction), dipaginasi (maks 3 halaman),
di-cache per kueri (dapat dilanjutkan), dengan batas konkurensi, retry+backoff, dan BATAS BIAYA (--max-requests).
Field mask HANYA yang perlu (id, nama, alamat, lokasi, tipe, status). TIDAK meminta rating, ulasan, jam buka, telepon, foto.

Kunci: env GOOGLE_PLACES_API_KEY atau berkas secrets/google_places.key (gitignored). Kunci tidak pernah dicetak atau disimpan di hasil.
Pemakaian:
  python tools/directory/places_discover.py plan                      # hitung jumlah kueri & perkiraan biaya (tanpa panggilan)
  python tools/directory/places_discover.py run --max-requests 4000   # jalankan (dapat diulang; kueri yang sudah di-cache dilewati)
  python tools/directory/places_discover.py run --province 35         # hanya satu provinsi
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ("places.id,places.displayName,places.formattedAddress,places.location,places.primaryType,places.types,"
              "places.businessStatus,nextPageToken")
KEYWORDS = [
    "perguruan pencak silat", "padepokan pencak silat", "tempat latihan pencak silat", "paguron silat", "sanggar pencak silat",
    "IPSI pencak silat", "PSHT Setia Hati Terate", "Pagar Nusa pencak silat", "Tapak Suci", "Merpati Putih silat",
    "Perisai Diri", "silek", "UKM pencak silat", "gelanggang silat",
]
MAX_PAGES = 3
PRICE_PER_1000_USD = 32.0   # Text Search Pro (perkiraan; periksa tarif terbaru). 5.000 pertama/bulan gratis pada tier tertentu.
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "research/pencak-silat/directory/raw/places"


def api_key() -> str:
    k = os.environ.get("GOOGLE_PLACES_API_KEY", "").strip()
    if not k and (ROOT / "secrets/google_places.key").exists():
        k = (ROOT / "secrets/google_places.key").read_text().strip()
    if not k:
        sys.exit("Kunci API tidak ditemukan (GOOGLE_PLACES_API_KEY atau secrets/google_places.key).")
    return k


def bbox(ring_sets) -> tuple[float, float, float, float]:
    pts = [p for r in ring_sets for p in r]
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)  # lat/lng


def queries(province: str | None):
    regions = json.loads((ROOT / "research/pencak-silat/directory/regions.json").read_text(encoding="utf-8"))
    for r in regions["regencies"]:
        if province and r["province_code"] != province or not r["rings"]:
            continue
        la0, lo0, la1, lo1 = bbox(r["rings"])
        short = r["name"].replace("Kabupaten Administrasi ", "").replace("Kota Administrasi ", "").replace("Kabupaten ", "").replace("Kota ", "")
        for kw in KEYWORDS:
            yield {"regency_code": r["code"], "keyword": kw, "text": f"{kw} {short}", "rect": [la0, lo0, la1, lo1]}


def qid(q) -> str:
    return hashlib.sha1(f"{q['regency_code']}|{q['text']}".encode()).hexdigest()[:16]


def call(key: str, body: dict, tries: int = 5) -> dict:
    data = json.dumps(body).encode()
    for i in range(tries):
        req = urllib.request.Request(ENDPOINT, data=data, headers={"Content-Type": "application/json", "X-Goog-Api-Key": key,
                                                                    "X-Goog-FieldMask": FIELD_MASK})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="ignore")[:300]
            if e.code in (429, 500, 503) and i < tries - 1:
                time.sleep(min(30, 2 ** i + 0.5 * i))
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg}") from None
        except (urllib.error.URLError, TimeoutError):
            if i < tries - 1:
                time.sleep(2 ** i)
                continue
            raise
    raise RuntimeError("gagal setelah retry")


def run_query(key: str, q: dict, budget: list) -> dict:
    out, token, pages = [], None, 0
    while pages < MAX_PAGES:
        if budget[0] <= 0:
            return {"incomplete": True}
        body = {"textQuery": q["text"], "languageCode": "id", "regionCode": "ID", "pageSize": 20,
                "locationRestriction": {"rectangle": {"low": {"latitude": q["rect"][0], "longitude": q["rect"][1]},
                                                       "high": {"latitude": q["rect"][2], "longitude": q["rect"][3]}}}}
        if token:
            body["pageToken"] = token
        budget[0] -= 1
        res = call(key, body)
        out += res.get("places", [])
        token = res.get("nextPageToken")
        pages += 1
        if not token:
            break
    return {"query": {k: q[k] for k in ("regency_code", "keyword", "text")}, "fetched_at": time.strftime("%Y-%m-%d"), "pages": pages, "places": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "run"])
    ap.add_argument("--province")
    ap.add_argument("--max-requests", type=int, default=2000, help="batas keras jumlah panggilan API (kontrol biaya)")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    qs = list(queries(a.province))
    todo = [q for q in qs if not (RAW / f"{qid(q)}.json").exists()]
    worst = len(todo) * MAX_PAGES
    print(f"kueri total {len(qs)} | belum di-cache {len(todo)} | panggilan terburuk ≈ {worst} (≈ US$ {worst * PRICE_PER_1000_USD / 1000:,.0f} bila semua halaman penuh; "
          f"biasanya jauh lebih sedikit karena sebagian besar kueri hanya 1 halaman)")
    if a.cmd == "plan":
        return
    key = api_key()
    RAW.mkdir(parents=True, exist_ok=True)
    budget = [a.max_requests]
    done = errs = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_query, key, q, budget): q for q in todo}
        for f in as_completed(futs):
            q = futs[f]
            try:
                r = f.result()
                if r.get("incomplete"):
                    continue
                (RAW / f"{qid(q)}.json").write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
                done += 1
            except Exception as e:  # noqa: BLE001
                errs += 1
                print(f"GAGAL {q['text']}: {str(e)[:160]}", file=sys.stderr)
            if (done + errs) % 50 == 0:
                print(f"  selesai {done} · gagal {errs} · sisa anggaran panggilan {budget[0]}", flush=True)
    print(f"selesai: {done} kueri baru, {errs} gagal, anggaran tersisa {budget[0]}. Jalankan lagi untuk melanjutkan bila belum tuntas.")


if __name__ == "__main__":
    main()
