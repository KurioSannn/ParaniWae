"""Pipeline direktori pencak silat nasional (hanya pustaka standar).

Search Discovery -> Raw Source Record -> Entity Extraction -> Normalization -> Classification -> Deduplication
-> Geocoding -> Coordinate Validation -> Source Verification -> keluaran (siap impor DB) + log job.

Masukan (research/pencak-silat/directory/):
  raw/osm_raw.json          snapshot Overpass (ODbL) + raw/q.overpassql (kueri yang dipakai)
  editorial_records.json    catatan riset web redaksi (+ sumber, organisasi induk)
  entity_localities.json    lokalitas entitas katalog -> kode kabupaten/kota
  regions.json              wilayah Kepmendagri 2025 (38 provinsi, 514 kab/kota, poligon)
  review_decisions.json     keputusan manual atas kandidat yang perlu ditinjau (opsional)
Keluaran:
  content/pencak-silat/directory/{places,organizations,heritage_areas}.json  (lolos verifikasi)
  research/pencak-silat/directory/build/{review_queue,rejected}.json
  research/pencak-silat/directory/jobs/<job_id>.json                         (log, error, statistik)
  research/pencak-silat/directory/search_plan.json                           (matriks cakupan)

TIDAK ada pemanggilan jaringan di sini: discovery jaringan dilakukan terpisah, satu kali, dan snapshot-nya disimpan.
Tidak ada koordinat tebakan: titik hanya dari fitur OSM; selain itu presisi = wilayah (kabupaten/kota).

Pemakaian: python tools/directory/pipeline.py [--repo .] [--job-id ID]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from urllib.parse import quote_plus
from datetime import datetime, timezone
from pathlib import Path

PIPELINE_VERSION = "1.0.0"
OSM_SNAPSHOT_DATE = "2026-11-21"
OSM_ATTRIBUTION = "© kontributor OpenStreetMap (ODbL 1.0)"
PUBLISH_MIN_CONFIDENCE = 0.45
DEDUP_RADIUS_M = 150.0

# ---------------------------------------------------------------- aturan klasifikasi (terdokumentasi di keywords.json)
STRONG = re.compile(
    r"pencak|silat|silek|pesilat|psht|setia hati|sh terate|ikspi|kera sakti|merpati putih|tapak suci|pagar nusa|"
    r"perisai diri|\bipsi\b|paguruan|gelanggang silat|maen pukulan|main pukulan", re.I)
SPORT_SILAT = re.compile(r"pencak_silat|\bsilat\b", re.I)
EXCL_PREFIX = re.compile(
    r"^(jalan|jl\.?|gang|gg\.?|sungai|terowongan|jembatan|perumahan|masjid|mesjid|mushala|mushola|musala|meunasah|"
    r"kantor kecamatan|kantor camat|kantor desa|saluran|pipa|pasar|terminal|puskesmas|rsud)\b", re.I)
EXCL_CONTAINS = re.compile(r"silatur|wasilatul|amtsilati|syahbandar|kesyahbandaran|plta|hipsi", re.I)
EXCL_TAGS = ("place", "natural", "boundary", "highway", "waterway", "route", "healthcare", "railway", "landuse")
REVIEW_WEAK = re.compile(r"padepokan|paguron|sanggar bela diri|panglipur|kala jengking", re.I)
SCHOOLISH = ("school:type_idn",)

CATEGORY_LABEL = {
    "perguruan_branch": "Cabang/ranting perguruan",
    "perguruan_center": "Pusat perguruan",
    "padepokan": "Padepokan",
    "training_center": "Pusat latihan",
    "ipsi": "Organisasi IPSI",
    "organization_office": "Kantor organisasi",
    "campus_unit": "Kampus/UKM",
    "community": "Sanggar/komunitas",
    "sports_venue": "Gelanggang olahraga",
    "cultural_center": "Pusat budaya & pelestarian",
    "cultural_landmark": "Monumen/penanda budaya",
}

PRECISION_LABEL = {
    "exact": "Titik tempat menurut data peta",
    "regency": "Lokasi pada tingkat kabupaten/kota (alamat latihan belum terdata)",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:80]


def tidy_name(n: str) -> str:
    n = re.sub(r"\s+", " ", n).strip()
    if n.isupper() or n.islower():
        small = {"dan", "di", "ke"}
        keep_upper = {"PSHT", "IPSI", "IKSPI", "KS", "UKM", "GOR", "SH", "UGM", "PP", "RT", "RW", "NTB", "TMII", "MP", "SUB."}
        words = []
        for w in n.split(" "):
            if w.upper() in keep_upper:
                words.append(w.upper())
            elif w.lower() in small and words:
                words.append(w.lower())
            else:
                words.append(w[:1].upper() + w[1:].lower())
        n = " ".join(words)
    n = re.sub(r"\bSekertariat\b", "Sekretariat", n, flags=re.I)
    n = re.sub(r"\bPedepokan\b", "Padepokan", n, flags=re.I)
    n = re.sub(r"\bPencaksilat\b", "Pencak Silat", n, flags=re.I)
    n = re.sub(r"\bPsht\b", "PSHT", n)
    return n


def haversine_m(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def point_in_ring(lat: float, lng: float, ring) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        yi, xi = ring[i]
        yj, xj = ring[j]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


class Regions:
    def __init__(self, data: dict):
        self.prov = {p["code"]: p for p in data["provinces"]}
        self.reg = {r["code"]: r for r in data["regencies"]}
        self.bbox = {}
        for r in data["regencies"]:
            pts = [p for ring in r["rings"] for p in ring]
            if pts:
                self.bbox[r["code"]] = (min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts))

    def short(self, code: str) -> str:
        return re.sub(r"^(Kabupaten Administrasi|Kota Administrasi|Kabupaten|Kota) ", "", self.reg[code]["name"])

    def named_in(self, name: str) -> list[str]:
        """Wilayah yang disebut eksplisit sebagai 'Cabang/Kota/Kabupaten X' pada nama (spasi diabaikan)."""
        flat = re.sub(r"\s+", "", name.lower())
        out = []
        for c in self.reg:
            sh = re.sub(r"\s+", "", self.short(c).lower())
            if len(sh) > 3 and re.search(rf"(cabang|kota|kabupaten|kab\.){re.escape(sh)}", flat):
                out.append(c)
        return out

    def distance_to_regency_m(self, lat: float, lng: float, code: str) -> float:
        if any(point_in_ring(lat, lng, ring) for ring in self.reg[code]["rings"]):
            return 0.0
        return min((haversine_m((lat, lng), (p[0], p[1])) for ring in self.reg[code]["rings"] for p in ring), default=1e12)

    def locate(self, lat: float, lng: float) -> str | None:
        hits = []
        for code, (a, b, c, d) in self.bbox.items():
            if a <= lat <= b and c <= lng <= d and any(point_in_ring(lat, lng, ring) for ring in self.reg[code]["rings"]):
                hits.append(code)
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:  # poligon disederhanakan bisa tumpang tindih di perbatasan: pilih ibu kota terdekat
            return min(hits, key=lambda c: haversine_m((lat, lng), (self.reg[c]["lat"], self.reg[c]["lng"])))
        # di luar semua poligon (garis pantai disederhanakan): ibu kota terdekat dalam 15 km, ditandai
        best = min(self.reg.values(), key=lambda r: haversine_m((lat, lng), (r["lat"], r["lng"])))
        return best["code"] if haversine_m((lat, lng), (best["lat"], best["lng"])) < 15000 else None


# ---------------------------------------------------------------- Open Location Code (Plus Code), pustaka standar
_OLC = "23456789CFGHJMPQRVWX"


def olc_recover(short: str, ref_lat: float, ref_lng: float) -> tuple[float, float] | None:
    """Plus Code pendek (mis. 'QQCH+FW2') -> titik tengah sel, dilengkapi dari titik acuan terdekat. None bila tidak valid."""
    code = short.strip().upper()
    if "+" not in code or len(code.split("+")[0]) != 4 or any(c not in _OLC + "+" for c in code):
        return None
    res = [20.0, 1.0, 0.05, 0.0025, 0.000125]

    def enc_prefix(lat: float, lng: float) -> str:
        la, lo, out = lat + 90.0, lng + 180.0, ""
        for r in res[:2]:
            out += _OLC[int(la // r) % 20] + _OLC[int(lo // r) % 20]
            la, lo = la % r, lo % r
        return out
    full = enc_prefix(ref_lat, ref_lng) + code
    digits = full.replace("+", "")
    lat, lng = -90.0, -180.0
    for i in range(0, min(len(digits), 10), 2):
        r = res[i // 2]
        lat += _OLC.index(digits[i]) * r
        lng += _OLC.index(digits[i + 1]) * r
    r = res[(min(len(digits), 10) // 2) - 1]
    lat, lng = lat + r / 2, lng + r / 2
    # prefiks 4 digit = sel 1°; bila hasil lebih dari setengah sel (0,5°) dari titik acuan, geser satu sel
    if abs(lat - ref_lat) > 0.5:
        lat += 1.0 if lat < ref_lat else -1.0
    if abs(lng - ref_lng) > 0.5:
        lng += 1.0 if lng < ref_lng else -1.0
    return round(lat, 6), round(lng, 6)


# ---------------------------------------------------------------- tahap
class Job:
    def __init__(self, job_id: str):
        self.id = job_id
        self.started = now_iso()
        self.stages: list[dict] = []
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def stage(self, name: str, **counts):
        self.stages.append({"stage": name, "at": now_iso(), **counts})

    def error(self, raw_id: str, stage: str, msg: str):
        self.errors.append({"raw_id": raw_id, "stage": stage, "message": msg})

    def warn(self, raw_id: str, stage: str, msg: str):
        self.warnings.append({"raw_id": raw_id, "stage": stage, "message": msg})


def discovery(root: Path, job: Job) -> list[dict]:
    """Snapshot -> Raw Source Record (satu per hasil)."""
    raws = []
    osm = json.loads((root / "raw/osm_raw.json").read_text(encoding="utf-8"))
    query = (root / "raw/q.overpassql").read_text(encoding="utf-8")
    qhash = hashlib.sha256(query.encode()).hexdigest()[:12]
    for e in osm["elements"]:
        rid = f"osm:{e['type']}/{e['id']}"
        raws.append({
            "raw_id": rid, "source_type": "openstreetmap", "source_url": f"https://www.openstreetmap.org/{e['type']}/{e['id']}",
            "query": f"overpass:{qhash}", "fetched_at": osm.get("osm3s", {}).get("timestamp_osm_base", OSM_SNAPSHOT_DATE),
            "payload": e,
        })
    ed = json.loads((root / "editorial_records.json").read_text(encoding="utf-8"))
    for r in ed["records"]:
        raws.append({"raw_id": f"editorial:{r['key']}", "source_type": "editorial_web", "source_url": None,
                     "query": "riset web redaksi 2026-11-21", "fetched_at": "2026-11-21", "payload": r})
    loc = json.loads((root / "entity_localities.json").read_text(encoding="utf-8"))
    for r in loc["places"]:
        raws.append({"raw_id": f"entity:{r['entity_id']}", "source_type": "research_catalog", "source_url": None,
                     "query": "katalog entitas riset (entities.json)", "fetched_at": "2026-11-20", "payload": r})
    n_lists = 0
    for f in sorted((root / "user_lists").glob("*.json")):
        ul = json.loads(f.read_text(encoding="utf-8"))
        for i, pl in enumerate(ul["places"]):
            raws.append({"raw_id": f"list:{ul['list_id']}#{i + 1}", "source_type": "map_listing", "source_url": None,
                         "query": f"daftar manual {ul['list_id']}", "fetched_at": ul["recorded_at"],
                         "payload": {**pl, "_ref": ul["reference_point"], "_list": ul["list_id"]}})
            n_lists += 1
    n_gp = 0
    seen_gp: set[str] = set()
    for f in sorted((root / "raw/places").glob("*.json")) if (root / "raw/places").exists() else []:
        qr = json.loads(f.read_text(encoding="utf-8"))
        for pl in qr.get("places", []):
            if pl["id"] in seen_gp:
                continue
            seen_gp.add(pl["id"])
            raws.append({"raw_id": f"gp:{pl['id']}", "source_type": "google_places", "source_url": None,
                         "query": qr["query"]["text"], "fetched_at": qr["fetched_at"], "payload": pl})
            n_gp += 1
    n_ov = 0
    ovp = root / "raw/overture/places.json"
    if ovp.exists():
        ov = json.loads(ovp.read_text(encoding="utf-8"))
        for pl in ov["places"]:
            raws.append({"raw_id": f"ov:{pl['id']}", "source_type": "overture", "source_url": None,
                         "query": f"overture {ov['release']}", "fetched_at": ov["release"].split(".")[0], "payload": pl})
            n_ov += 1
    job.stage("discovery", raw_records=len(raws), google_places=n_gp, overture=n_ov, osm=len(osm["elements"]), editorial=len(ed["records"]), catalog=len(loc["places"]), user_lists=n_lists)
    return raws


def extract_osm(raw: dict) -> dict:
    e = raw["payload"]
    t = e.get("tags", {})
    lat = e.get("lat", e.get("center", {}).get("lat"))
    lng = e.get("lon", e.get("center", {}).get("lon"))
    addr = {k[5:]: v for k, v in t.items() if k.startswith("addr:")}
    return {
        "raw_id": raw["raw_id"], "name": t.get("name", ""), "tags": t, "lat": lat, "lng": lng,
        "address": addr, "source_type": "openstreetmap", "source_url": raw["source_url"], "fetched_at": raw["fetched_at"],
    }


def classify_osm(x: dict) -> tuple[str, str, str | None]:
    """-> (keputusan accept|review|reject, alasan, kategori)."""
    n, t = tidy_name(x["name"]), x["tags"]
    if not n.strip():
        return "reject", "tanpa nama", None
    if any(k in t for k in EXCL_TAGS) or t.get("amenity") == "place_of_worship" or t.get("type") == "route":
        return "reject", "jenis fitur bukan tempat latihan/organisasi (toponimi, ibadah, rute, kesehatan)", None
    if EXCL_PREFIX.search(n) or EXCL_CONTAINS.search(n):
        return "reject", "nama cocok kata kunci tetapi pola pengecualian (jalan, masjid, kesyahbandaran, dll.)", None
    strong = bool(STRONG.search(n))
    sport = bool(SPORT_SILAT.search(t.get("sport", "")))
    if not strong and not sport:
        if REVIEW_WEAK.search(n) and (t.get("leisure") or t.get("amenity") in ("community_centre", "dojo", "school")):
            return "review", "istilah lemah (padepokan/paguron) tanpa bukti pencak silat pada data", None
        return "reject", "tidak ada bukti pencak silat pada nama atau tag", None
    if any(k in t for k in SCHOOLISH) and not re.search(r"psht|sekretariat", n, re.I):
        return "review", "bangunan sekolah; perlu bukti bahwa ruang ini dipakai latihan", None
    if t.get("tourism") == "attraction" and not t.get("leisure"):
        return "review", "objek wisata; perlu konfirmasi jadwal/lokasi latihan", None
    nl = n.lower()
    if t.get("historic") == "monument" or "prasasti" in nl or "tugu" in nl or "monumen" in nl:
        return "accept", "penanda budaya terkait perguruan", "cultural_landmark"
    if "museum" == t.get("tourism") and "padepokan" in nl:
        return "accept", "padepokan nasional (museum & pusat budaya)", "cultural_center"
    if re.search(r"\bipsi\b", nl):
        return "accept", "kantor IPSI", "ipsi"
    if re.search(r"sekretariat|pengurus|kantor", nl) or t.get("office"):
        return "accept", "kantor/sekretariat organisasi pencak silat", "organization_office"
    if re.search(r"rayon|ranting|cabang|sub\.", nl):
        return "accept", "unit wilayah perguruan", "perguruan_branch"
    if re.search(r"training center|pusat latihan", nl) or t.get("amenity") == "training":
        return "accept", "pusat latihan", "training_center"
    if sport and not strong:
        return "accept", "gelanggang olahraga yang mencantumkan pencak silat", "sports_venue"
    if re.search(r"gelanggang|gor\b", nl):
        return "accept", "gelanggang pencak silat", "sports_venue"
    if "sanggar" in nl:
        return "accept", "sanggar pencak silat", "community"
    if "padepokan" in nl or "paguruan" in nl or t.get("amenity") == "dojo":
        return "accept", "padepokan/tempat latihan", "padepokan"
    if re.search(r"psht|ikspi|merpati putih|tapak suci|pagar nusa|perisai diri", nl) or t.get("leisure") == "sports_centre":
        return "accept", "tempat perguruan", "perguruan_branch"
    return "review", "bukti nama ada tetapi kategori tidak jelas", None


GP_STORE_TYPES = {"store", "clothing_store", "sporting_goods_store", "shoe_store", "convenience_store", "shopping_mall", "restaurant",
                  "cafe", "lodging", "hotel", "place_of_worship", "mosque", "hospital", "doctor", "pharmacy", "bank", "gas_station",
                  "real_estate_agency", "school", "primary_school", "secondary_school", "university", "tourist_attraction", "park"}
GP_OK_TYPES = {"martial_arts_school", "sports_club", "sports_school", "gym", "fitness_center", "sports_complex", "stadium", "community_center",
               "association_or_organization", "non_profit_organization", "cultural_center", "performing_arts_theater"}


OTHER_ARTS = re.compile(r"\b(judo|taekwondo|tae kwon do|karate|kempo|aikido|muay|boxing|tinju|jiu.?jitsu|wushu|kickboxing|mma|capoeira|krav)\b", re.I)
NOT_VENUE = re.compile(r"vihara|gereja|paroki|panti|wedding|resort|hotel|villa|homestay|kost|restoran|warung|cafe|kafe|toko|apotek|bank|pasar|"
                       r"bookstore|library|perpustakaan|rumah sakit|klinik|masjid|musholla|mushola|pondok pesantren|pesantren|"
                       r"\bsd\b|\bsdn\b|\bsmp\b|\bsmpn\b|\bsma\b|\bsman\b|\bsmk\b|\bmi[ns]?\b|\bmts\b|sekolah|madrasah|panwaslu|kecamatan|kelurahan|martabak|farm|kantor desa|puskesmas|\bpt\b|\bcv\b", re.I)
SILAT_ORG = re.compile(r"iks\.?\s?pi|kera sakti|psht|setia hati terate|pagar nusa|tapak suci|merpati putih|perisai (diri|putih)|persinas|satria muda|"
                       r"inti ombak|tunggal hati|pro patria|bakti negara|garuda putih|kalimasada|sinar putih|ipsi", re.I)  # cimande/cikalong/beksi sengaja tidak ada: sering nama desa/kecamatan
HARD_NOT_VENUE = re.compile(r"\bpt\b|\bcv\b|\bssb\b|sepak ?bola|football|futsal|klub bola|posyandu|distro|\bcafe\b|\bkafe\b|warung|\btoko\b|martabak|wedding|hotel|villa|restoran|bookstore|apotek|barbershop|salon|laundry|bengkel|photography|studio foto", re.I)
WEAK_WORD = re.compile(r"\b(padepokan|paguron|sasana|sanggar|perguruan|bela ?diri|beladiri|kuntau|langga|gelanggang)\b", re.I)


def classify_places(name: str, pl: dict) -> tuple[str, str, str | None]:
    """Saringan relevansi untuk sumber POI yang berisik (Places API / Overture).

    Diterima otomatis hanya bila nama menyebut pencak silat atau perguruan silat yang dikenal. Kata umum (padepokan, sasana,
    sanggar, perguruan) hanya diterima bila kategori sumber 'martial arts'; selain itu masuk antrean tinjauan, bukan publik.
    """
    n = tidy_name(name)
    types = set(pl.get("types", [])) | ({pl["primaryType"]} if pl.get("primaryType") else set())
    if pl.get("businessStatus") in ("CLOSED_PERMANENTLY",):
        return "reject", "ditandai tutup permanen", None
    if EXCL_PREFIX.search(n) or EXCL_CONTAINS.search(n):
        return "reject", "nama cocok pola pengecualian", None
    silat_named = bool(re.search(r"pencak|silat|silek|pesilat|paguruan|maen pukulan|main pukulan|penca\b", n, re.I)) or bool(SILAT_ORG.search(n))
    martial = "martial_arts_school" in types
    if types & {"store", "clothing_store", "sporting_goods_store", "shoe_store"} and not martial:
        return "reject", "toko/perlengkapan, bukan tempat latihan", None
    if HARD_NOT_VENUE.search(n):
        return "reject", "usaha/layanan, bukan tempat latihan", None
    if NOT_VENUE.search(n) and not silat_named:
        return "reject", "bukan tempat latihan (ibadah/usaha/penginapan/dll.)", None
    if OTHER_ARTS.search(n) and not silat_named:
        return "reject", "bela diri lain, bukan pencak silat", None
    weak = bool(WEAK_WORD.search(n))
    if not silat_named:
        if martial and weak:
            return "review", "kategori bela diri + kata umum, tetapi nama tidak menyebut pencak silat", None
        if martial:
            return "review", "kategori bela diri tetapi nama tidak menyebut pencak silat (bisa bela diri lain)", None
        return "reject", "nama dan kategori tidak menunjukkan pencak silat", None
    nl = n.lower()
    if re.search(r"\bipsi\b", nl):
        return "accept", "organisasi/kantor IPSI", "ipsi"
    if re.search(r"universitas|\bukm\b|kampus|mahasiswa", nl):
        return "accept", "unit kampus", "campus_unit"
    if re.search(r"gor\b|gelanggang|stadion|gedung olahraga", nl):
        return "accept", "gelanggang", "sports_venue"
    if re.search(r"sekretariat|kantor|pengurus|dpc|dpd|pengcab|pengkab|pengkot", nl):
        return "accept", "kantor/sekretariat", "organization_office"
    if "padepokan" in nl:
        return "accept", "padepokan", "padepokan"
    if re.search(r"sanggar|paguron|sasana", nl):
        return "accept", "sanggar/paguron", "community"
    return "accept", "tempat perguruan", "perguruan_branch"


def normalize_osm(x: dict, orgs: list[dict], decision: tuple) -> dict:
    t = x["tags"]
    name = tidy_name(x["name"])
    parent = next((o["key"] for o in orgs if re.search(o["match"], x["name"], re.I)), None)
    sports = [s.strip().lower() for s in re.split(r"[;,]", t.get("sport", "")) if s.strip()]
    venue = "multi_sport" if len(sports) > 1 else ("building" if t.get("building") else "area" if t.get("area") else "point")
    return {
        "official_name": name, "display_name": name, "aliases": [tidy_name(v) for k, v in t.items() if k in ("short_name", "alt_name", "official_name") and tidy_name(v) != name],
        "place_category": decision[2], "organization_key": parent,
        "latitude": x["lat"], "longitude": x["lng"], "location_precision": "exact",
        "full_address": ", ".join(v for k, v in x["address"].items() if k in ("full", "street", "housename", "subdistrict", "district", "city", "postcode")) or None,
        "district": (x["address"].get("district") or "").replace("Kec. ", "") or None,
        "village": x["address"].get("subdistrict") or None,
        "venue_type": venue,
        "is_training_location": decision[2] in ("padepokan", "training_center", "perguruan_branch", "community", "campus_unit") or None,
        "is_organization_office": decision[2] in ("organization_office", "ipsi") or bool(re.search(r"sekretariat|kantor|pengurus", name, re.I)),
        "sports_listed": sports or None,
        "osm_opening_hours": t.get("opening_hours"),  # tidak ditampilkan sebagai jadwal latihan
        "evidence": [f"Nama/tag OSM: {x['name']}" + (f" (sport={t['sport']})" if t.get("sport") else "")],
        "classification_reason": decision[1],
        "sources": [{
            "source_type": "openstreetmap", "url": x["source_url"], "title": f"OpenStreetMap {x['raw_id'][4:]}",
            "publisher": "OpenStreetMap", "license": "ODbL 1.0", "attribution": OSM_ATTRIBUTION,
            "retrieved_at": x["fetched_at"][:10], "supports": ["nama", "koordinat"] + (["alamat"] if x["address"] else []),
        }],
        "raw_ids": [x["raw_id"]],
    }


def confidence(p: dict) -> float:
    types = {s["source_type"] for s in p["sources"]}
    base = max({"official_site": 0.75, "academic": 0.7, "heritage_record": 0.7, "openstreetmap": 0.55, "news": 0.5, "map_listing": 0.55, "google_places": 0.5, "overture": 0.5}.get(t, 0.4) for t in types)
    score = base
    publishers = {(s.get("publisher") or s.get("url") or "").lower() for s in p["sources"]}
    if len(p["sources"]) >= 2 and len(publishers) >= 2:
        score += 0.1  # dua sumber dari penerbit berbeda
    if p["place_category"] in ("sports_venue",):
        score -= 0.05  # pencak silat hanya tercantum di antara cabang lain
    if p["location_precision"] == "exact":
        score += 0.05
    else:
        score -= 0.1
    return round(max(0.0, min(0.95, score)), 2)


def run(repo: Path, job_id: str | None = None) -> dict:
    root = repo / "research/pencak-silat/directory"
    out_dir = repo / "content/pencak-silat/directory"
    build = root / "build"
    for d in (out_dir, build, root / "jobs"):
        d.mkdir(parents=True, exist_ok=True)
    job = Job(job_id or "dir-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    regions = Regions(json.loads((root / "regions.json").read_text(encoding="utf-8")))
    ed = json.loads((root / "editorial_records.json").read_text(encoding="utf-8"))
    loc = json.loads((root / "entity_localities.json").read_text(encoding="utf-8"))
    ents = {e["id"]: e for e in json.loads((repo / "research/pencak-silat/traditions/entities.json").read_text(encoding="utf-8"))["entities"]}
    ledger = {s["id"]: s for s in json.loads((repo / "research/pencak-silat/sources/sources.json").read_text(encoding="utf-8"))["sources"]}
    for s in ed["sources"]:
        ledger[s["id"]] = s
    decisions_path = root / "review_decisions.json"
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))["decisions"] if decisions_path.exists() else {}
    orgs = ed["organizations"]

    raws = discovery(root, job)

    # ---- extraction + classification + normalization
    candidates, review, rejected = [], [], []
    for raw in raws:
        try:
            if raw["source_type"] == "openstreetmap":
                x = extract_osm(raw)
                dec = classify_osm(x)
                manual = decisions.get(raw["raw_id"])
                if manual:
                    dec = (manual["decision"], f"keputusan peninjau: {manual['reason']}", manual.get("category", dec[2]))
                if dec[0] == "reject":
                    rejected.append({"raw_id": raw["raw_id"], "name": x["name"], "reason": dec[1]})
                    continue
                if dec[0] == "review":
                    review.append({"raw_id": raw["raw_id"], "name": x["name"], "reason": dec[1], "tags": x["tags"],
                                   "lat": x["lat"], "lng": x["lng"], "source_url": x["source_url"]})
                    continue
                candidates.append(normalize_osm(x, orgs, dec))
            elif raw["source_type"] == "editorial_web":
                r = raw["payload"]
                srcs = [ledger[s] for s in r["source_ids"] if s in ledger]
                if len(srcs) != len(r["source_ids"]):
                    job.error(raw["raw_id"], "extraction", "source_id tidak ada di ledger")
                    continue
                candidates.append({
                    "official_name": r["official_name"], "display_name": r["official_name"], "aliases": r.get("aliases", []),
                    "place_category": r["place_category"], "organization_key": r.get("organization_key"),
                    "latitude": None, "longitude": None, "location_precision": "regency", "regency_code": r["regency_code"],
                    "full_address": r.get("full_address"), "district": r.get("district"), "village": r.get("village"),
                    "venue_type": None, "is_training_location": r.get("is_training_location"),
                    "is_organization_office": r.get("is_organization_office"),
                    "contact_email": r.get("contact_email"), "official_website": r.get("official_website"),
                    "training_categories": r.get("training_categories"), "data_conflicts": r.get("data_conflicts"),
                    "evidence": [r["training_evidence"]] if r.get("training_evidence") else [],
                    "classification_reason": "catatan riset web redaksi", "match_osm": r.get("match_osm"),
                    "entity_id": r.get("entity_id"),
                    "sources": [_ledger_source(s) for s in srcs], "raw_ids": [raw["raw_id"]],
                })
            elif raw["source_type"] == "google_places":
                pl = raw["payload"]
                name = (pl.get("displayName") or {}).get("text", "")
                loc_ = pl.get("location") or {}
                dec = classify_places(name, pl)
                if dec[0] == "reject":
                    rejected.append({"raw_id": raw["raw_id"], "name": name, "reason": dec[1]})
                    continue
                if dec[0] == "review" or "latitude" not in loc_:
                    review.append({"raw_id": raw["raw_id"], "name": name, "reason": dec[1] if dec[0] == "review" else "tanpa koordinat",
                                   "types": pl.get("types", [])[:6], "lat": loc_.get("latitude"), "lng": loc_.get("longitude")})
                    continue
                parent = next((o["key"] for o in orgs if re.search(o["match"], name, re.I)), None)
                candidates.append({
                    "official_name": tidy_name(name), "display_name": tidy_name(name), "aliases": [], "place_category": dec[2],
                    "organization_key": parent, "latitude": loc_["latitude"], "longitude": loc_["longitude"], "location_precision": "exact",
                    "full_address": pl.get("formattedAddress"), "district": None, "village": None, "venue_type": None,
                    "is_training_location": dec[2] in ("padepokan", "training_center", "perguruan_branch", "community", "campus_unit") or None,
                    "is_organization_office": None,
                    "evidence": [f"Ditemukan pada pencarian tempat untuk '{raw['query']}'; tipe: {', '.join(pl.get('types', [])[:3])}."],
                    "classification_reason": dec[1],
                    "sources": [{"source_type": "google_places", "source_id": f"gp:{pl['id']}", "url": f"https://www.google.com/maps/place/?q=place_id:{pl['id']}",
                                 "title": "Google Maps (Places API)", "publisher": "Google Maps", "license": "Ketentuan Google Maps Platform; segarkan data berkala",
                                 "attribution": "Data tempat: Google Maps", "retrieved_at": raw["fetched_at"], "supports": ["nama", "alamat", "koordinat"]}],
                    "raw_ids": [raw["raw_id"]],
                })
            elif raw["source_type"] == "overture":
                pl = raw["payload"]
                name = pl.get("name") or ""
                fake = {"types": [(pl.get("category") or "")], "primaryType": pl.get("category") or "", "businessStatus": "CLOSED_PERMANENTLY" if pl.get("operating_status") == "permanently_closed" else ""}
                cat_l = (pl.get("category") or "").lower()
                if "martial" in cat_l or "dojo" in cat_l or "self_defense" in cat_l:
                    fake["types"] = ["martial_arts_school"]
                elif any(w in cat_l for w in ("store", "shop", "retail", "clothing", "equipment")):
                    fake["types"] = ["store"]
                dec = classify_places(name, fake)
                if dec[0] == "reject":
                    rejected.append({"raw_id": raw["raw_id"], "name": name, "reason": dec[1]})
                    continue
                if dec[0] == "review" or pl.get("lat") is None or (pl.get("confidence") or 0) < 0.3:
                    review.append({"raw_id": raw["raw_id"], "name": name, "reason": dec[1] if dec[0] == "review" else "confidence sumber rendah/tanpa titik",
                                   "lat": pl.get("lat"), "lng": pl.get("lng")})
                    continue
                parent = next((o["key"] for o in orgs if re.search(o["match"], name, re.I)), None)
                ds = sorted(set(pl.get("datasets") or []))
                candidates.append({
                    "official_name": tidy_name(name), "display_name": tidy_name(name), "aliases": [], "place_category": dec[2],
                    "organization_key": parent, "latitude": pl["lat"], "longitude": pl["lng"], "location_precision": "exact",
                    "full_address": pl.get("address") or ", ".join(x for x in (pl.get("locality"), pl.get("region")) if x) or None,
                    "district": None, "village": None, "venue_type": None,
                    "is_training_location": dec[2] in ("padepokan", "training_center", "perguruan_branch", "community", "campus_unit") or None,
                    "is_organization_office": None,
                    "evidence": [f"Tercatat di Overture Maps Places (kategori {pl.get('category') or '-'}; sumber data: {', '.join(ds) or '-'})."],
                    "classification_reason": dec[1], "source_confidence": pl.get("confidence"),
                    "sources": [{"source_type": "overture", "source_id": f"ov:{pl['id']}", "url": f"https://explore.overturemaps.org/#17/{pl['lat']:.5f}/{pl['lng']:.5f}",
                                 "title": "Overture Maps Foundation — Places", "publisher": "Overture Maps Foundation", "license": "CDLA Permissive 2.0 (atribusi: Overture Maps Foundation)",
                                 "attribution": "Data tempat: Overture Maps Foundation", "retrieved_at": raw["fetched_at"], "supports": ["nama", "koordinat"] + (["alamat"] if pl.get("address") else [])}],
                    "raw_ids": [raw["raw_id"]],
                })
            elif raw["source_type"] == "map_listing":
                r = raw["payload"]
                lat = lng = None
                if r.get("plus_code"):
                    ll = olc_recover(r["plus_code"], r["_ref"]["lat"], r["_ref"]["lng"])
                    if ll:
                        lat, lng = ll
                    else:
                        job.warn(raw["raw_id"], "extraction", "Plus Code tidak valid; dipakai tingkat wilayah")
                gmaps = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(r["name"])
                candidates.append({
                    "official_name": r["name"], "display_name": r["name"], "aliases": [], "place_category": r["category"],
                    "organization_key": r.get("org"), "latitude": lat, "longitude": lng,
                    "location_precision": "exact" if lat is not None else "regency", "regency_code": r["regency_code"],
                    "full_address": r.get("address"), "district": None, "village": None, "venue_type": None,
                    "is_training_location": True, "is_organization_office": None,
                    "evidence": ["Tercatat sebagai tempat latihan pencak silat pada pencarian peta (dicatat manual tim, 2026-11-21)."],
                    "classification_reason": "daftar manual tim (nama & alamat saja)",
                    "sources": [{"source_type": "map_listing", "url": gmaps, "title": "Pencarian peta (dicatat manual tim SILATARA)",
                                 "publisher": "Google Maps", "license": "Hanya fakta nama/alamat; peringkat, ulasan, jam, dan kontak tidak disimpan",
                                 "attribution": None, "retrieved_at": raw["fetched_at"], "supports": ["nama", "alamat"] + (["koordinat (Plus Code)"] if lat is not None else [])}],
                    "raw_ids": [raw["raw_id"]],
                })
            else:  # research_catalog
                r = raw["payload"]
                e = ents.get(r["entity_id"])
                if not e:
                    job.error(raw["raw_id"], "extraction", "entity_id tidak ditemukan")
                    continue
                srcs = [ledger[s] for s in e.get("source_ids", []) if s in ledger]
                cat = {"perguruan": "perguruan_center", "training_place": "padepokan", "community": "community"}.get(e["category"], "community")
                candidates.append({
                    "official_name": e["name"], "display_name": e["name"], "aliases": e.get("public_aliases") or [],
                    "place_category": cat, "organization_key": None, "entity_id": e["id"],
                    "latitude": None, "longitude": None, "location_precision": "regency", "regency_code": r["regency_code"],
                    "full_address": None, "district": None, "village": None, "locality_text": r["locality_text"],
                    "venue_type": None, "is_training_location": None, "is_organization_office": None,
                    "evidence": [r["role"]], "classification_reason": "entitas katalog riset dengan lokalitas dari sumber",
                    "sources": [_ledger_source(s) for s in srcs], "raw_ids": [raw["raw_id"]],
                })
        except Exception as exc:  # noqa: BLE001 — dicatat per record, job tetap jalan
            job.error(raw["raw_id"], "extraction", f"{type(exc).__name__}: {exc}")
    job.stage("extraction+classification", candidates=len(candidates), review=len(review), rejected=len(rejected))

    # ---- deduplication
    merged: list[dict] = []
    dup_log = []
    for c in candidates:
        tgt = None
        for m in merged:
            same_osm = c.get("match_osm") and any(rid == f"osm:{c['match_osm']}" for rid in m["raw_ids"])
            close = (c["latitude"] is not None and m["latitude"] is not None
                     and haversine_m((c["latitude"], c["longitude"]), (m["latitude"], m["longitude"])) < DEDUP_RADIUS_M
                     and _name_key(c["official_name"]) == _name_key(m["official_name"]))
            same_entity = c.get("entity_id") and c.get("entity_id") == m.get("entity_id")
            if same_osm or close or same_entity:
                tgt = m
                break
        if tgt is None:
            merged.append(c)
            continue
        dup_log.append({"kept": tgt["raw_ids"][0], "merged": c["raw_ids"][0], "reason": "osm-match" if c.get("match_osm") else "nama+jarak" if c["latitude"] else "entitas sama"})
        # gabung: sumber, raw id, alias; atribut editorial melengkapi (tidak menimpa koordinat OSM)
        tgt["sources"] += [s for s in c["sources"] if s not in tgt["sources"]]
        tgt["raw_ids"] += c["raw_ids"]
        tgt["aliases"] = sorted(set(tgt["aliases"]) | set(c["aliases"]) | ({c["official_name"]} - {tgt["official_name"]}))
        for k in ("full_address", "organization_key", "entity_id", "contact_email", "official_website", "district", "village"):
            if c.get(k) and not tgt.get(k):
                tgt[k] = c[k]
        if c["place_category"] and c.get("match_osm"):
            tgt["official_name"] = tgt["display_name"] = c["official_name"]
            tgt["place_category"] = c["place_category"]
        tgt["evidence"] += [e for e in c["evidence"] if e not in tgt["evidence"]]
    job.stage("deduplication", before=len(candidates), after=len(merged), merged=len(dup_log))

    # ---- geocoding + coordinate validation
    places = []
    for p in merged:
        rid = p["raw_ids"][0]
        if p["location_precision"] == "exact":
            if p["latitude"] is None or not (-11.5 <= p["latitude"] <= 6.5 and 94.5 <= p["longitude"] <= 141.5):
                job.error(rid, "coordinate_validation", "koordinat kosong atau di luar Indonesia")
                continue
            code = regions.locate(p["latitude"], p["longitude"])
            if not code:
                rejected.append({"raw_id": rid, "name": p["official_name"], "reason": "titik di luar wilayah Indonesia (mis. negara tetangga) atau di laut"})
                continue
            p["regency_code"] = code
            p["coordinate_check"] = "point_in_regency_polygon"
            named = regions.named_in(p["official_name"])
            if named and code not in named:
                near = [c for c in named if regions.distance_to_regency_m(p["latitude"], p["longitude"], c) < 3000]
                if near:
                    p["regency_code"] = near[0]
                    p["coordinate_check"] = "near_boundary_named_regency"
                    job.warn(rid, "coordinate_validation", f"titik dekat batas; wilayah mengikuti nama ({near[0]})")
                else:
                    p.setdefault("data_conflicts", []).append(
                        f"Nama menyebut {regions.short(named[0])}, sedangkan titik di peta berada di {regions.reg[code]['name']}.")
        else:
            code = p.get("regency_code")
            if code not in regions.reg:
                job.error(rid, "geocoding", f"kode wilayah tidak dikenal: {code}")
                continue
            r = regions.reg[code]
            # penanda area: ibu kota kabupaten/kota, ditandai jelas sebagai presisi wilayah (bukan alamat)
            p["latitude"], p["longitude"] = r["lat"], r["lng"]
            p["coordinate_check"] = "regency_capital_area_marker"
        p["province_code"] = p["regency_code"].split(".")[0]
        p["regency_name"] = regions.reg[p["regency_code"]]["name"]
        p["province_name"] = regions.prov[p["province_code"]]["name"]
        places.append(p)
    job.stage("geocoding+coordinate_validation", places=len(places))

    # ---- source verification + confidence
    final = []
    for p in places:
        rid = p["raw_ids"][0]
        if not p["sources"]:
            job.error(rid, "source_verification", "tanpa sumber")
            continue
        p["confidence"] = confidence(p)
        if p["confidence"] < PUBLISH_MIN_CONFIDENCE:
            review.append({"raw_id": rid, "name": p["official_name"], "reason": f"confidence {p['confidence']} < {PUBLISH_MIN_CONFIDENCE}"})
            continue
        base = slugify(f"{p['display_name']} {p['regency_name'].replace('Kabupaten ', '').replace('Kota Administrasi ', '').replace('Kota ', '')}")
        slug, k = base, 2
        while any(f["slug"] == slug for f in final):
            slug, k = f"{base}-{k}", k + 1
        p["slug"] = slug
        p["external_key"] = rid
        p["category_label"] = CATEGORY_LABEL.get(p["place_category"], p["place_category"])
        p["precision_label"] = PRECISION_LABEL[p["location_precision"]]
        p["public_access"] = "unknown"
        p["status"] = "active_unverified"
        p["last_verified_at"] = None
        final.append(p)
    job.stage("source_verification", published=len(final), review_total=len(review))

    # ---- heritage areas
    heritage = []
    for h in loc["heritage_areas"]:
        e = ents.get(h["entity_id"])
        if not e:
            job.error(h["entity_id"], "heritage", "entity_id tidak ditemukan")
            continue
        heritage.append({
            "entity_id": e["id"], "name": e["name"], "category": e["category"], "regency_codes": h["regency_codes"],
            "regencies": [regions.reg[c]["name"] for c in h["regency_codes"]], "locality_text": h["locality_text"],
            "points": [{"lat": regions.reg[c]["lat"], "lng": regions.reg[c]["lng"], "regency_code": c} for c in h["regency_codes"]],
            "public_note": e.get("public_note"), "sources": [_ledger_source(ledger[s]) for s in e.get("source_ids", []) if s in ledger],
        })

    organizations = []
    for o in orgs:
        o2 = {k: v for k, v in o.items() if k != "match"}
        o2["place_count"] = sum(1 for p in final if p.get("organization_key") == o["key"])
        if o.get("entity_id") and o["entity_id"] in ents:
            o2["sources"] = [_ledger_source(ledger[s]) for s in ents[o["entity_id"]].get("source_ids", []) if s in ledger]
        else:
            o2["sources"] = []
        organizations.append(o2)

    meta = {"pipeline_version": PIPELINE_VERSION, "job_id": job.id, "generated_at": now_iso(),
            "attribution": [OSM_ATTRIBUTION, "Wilayah: Kepmendagri No 300.2.2-2138 Tahun 2025 (dataset cahyadsn/wilayah, MIT)"]}
    _dump(out_dir / "places.json", {**meta, "schema": "silatara.directory.places/v1", "places": final})
    _dump(out_dir / "organizations.json", {**meta, "schema": "silatara.directory.organizations/v1", "organizations": organizations})
    _dump(out_dir / "heritage_areas.json", {**meta, "schema": "silatara.directory.heritage-areas/v1", "areas": heritage})
    _dump(build / "review_queue.json", {**meta, "items": review})
    _dump(build / "rejected.json", {**meta, "items": rejected})
    plan = search_plan(regions, final, review)
    _dump(root / "search_plan.json", plan)
    summary = {
        "job_id": job.id, "pipeline_version": PIPELINE_VERSION, "started_at": job.started, "finished_at": now_iso(),
        "stages": job.stages, "errors": job.errors, "warnings": job.warnings, "duplicates": dup_log,
        "result": {"places": len(final), "review": len(review), "rejected": len(rejected), "heritage_areas": len(heritage),
                   "organizations": len(organizations),
                   "provinces_with_places": len({p["province_code"] for p in final}),
                   "regencies_with_places": len({p["regency_code"] for p in final}),
                   "precision": {k: sum(1 for p in final if p["location_precision"] == k) for k in PRECISION_LABEL}},
        "import_status": "built_not_imported",
    }
    _dump(root / "jobs" / f"{job.id}.json", summary)
    return summary


def search_plan(regions: Regions, places: list[dict], review: list[dict]) -> dict:
    """Matriks provinsi × kab/kota × kategori kata kunci × jenis sumber, dengan status jujur per sel."""
    src_status = {
        "openstreetmap": {"status": "done", "method": "1 kueri Overpass nasional (regex kata kunci + tag sport), snapshot 2026-11-21"},
        "research_catalog": {"status": "done", "method": "lokalitas entitas dari berkas UNESCO & publikasi akademik"},
        "editorial_web": {"status": "partial", "method": "riset web untuk pusat organisasi besar (PSHT, Tapak Suci, Merpati Putih, IPSI)"},
        "situs_ipsi_daerah": {"status": "not_run"}, "pemerintah_daerah": {"status": "not_run"}, "dispora": {"status": "not_run"},
        "dinas_kebudayaan": {"status": "not_run"}, "berita": {"status": "partial"}, "kampus_ukm": {"status": "partial"},
        "kiriman_pengelola": {"status": "open", "method": "formulir kiriman di situs"},
        "google_maps": {"status": "link_only", "method": "tautan pencarian eksternal; konten Google tidak disimpan"},
    }
    cats = ["jenis_tempat", "organisasi", "istilah_lokal", "aliran_tradisi"]
    rows = []
    for code, r in sorted(regions.reg.items()):
        found = [p["slug"] for p in places if p["regency_code"] == code]
        rows.append({"regency_code": code, "regency": r["name"], "province_code": code.split(".")[0],
                     "province": regions.prov[code.split(".")[0]]["name"], "places_found": len(found), "place_slugs": found})
    return {
        "schema": "silatara.directory.search-plan/v1", "generated_at": now_iso(),
        "dimensions": {"provinces": len(regions.prov), "regencies": len(regions.reg), "keyword_categories": cats, "source_types": list(src_status)},
        "source_status": src_status,
        "cells_total": len(regions.reg) * len(cats) * len(src_status),
        "regencies": rows,
        "regencies_with_results": sum(1 for x in rows if x["places_found"]),
        "review_pending": len(review),
    }


def _name_key(n: str) -> str:
    return re.sub(r"[^a-z0-9]", "", n.lower())


def _ledger_source(s: dict) -> dict:
    t = s.get("type", "")
    st = ("official_site" if t in ("official_site", "official_document") else "heritage_record" if "unesco" in s["id"] or t == "heritage_record"
          else "news" if t == "news" else "academic")
    return {"source_type": st, "source_id": s["id"], "url": s.get("url"), "title": s.get("title"),
            "publisher": s.get("author_or_publisher"), "year": s.get("year"), "license": s.get("license"),
            "read_status": s.get("read_status"), "supports": s.get("supports", [])[:3]}


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--job-id")
    a = ap.parse_args()
    res = run(Path(a.repo), a.job_id)
    print(json.dumps(res["result"], ensure_ascii=False))
    if res["errors"]:
        print(f"{len(res['errors'])} error (lihat log job)", file=sys.stderr)
