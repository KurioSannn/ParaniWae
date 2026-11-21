# Kontrak Direktori Nasional

Peta dan daftar tempat latihan pencak silat. Data berasal dari sumber yang boleh diolah; setiap tempat menyimpan sumbernya secara terstruktur (`directory_place_sources`), tetapi **halaman publik tidak menampilkan daftar rujukan** (arahan pemilik produk 2026-11-21); hanya atribusi lisensi satu baris.

## Pipeline (`tools/directory/pipeline.py`, tanpa jaringan)
Discovery -> raw record -> ekstraksi -> normalisasi -> klasifikasi -> deduplikasi (nama+radius 150 m / entitas sama) -> geocoding -> validasi koordinat (titik-dalam-poligon kab/kota Kepmendagri 2025) -> verifikasi sumber & skor kepercayaan -> keluaran + log job (`research/pencak-silat/directory/jobs/*.json`).

| Sumber | Cara | Catatan |
|---|---|---|
| Wilayah (38 prov., 514 kab/kota) | `build_regions.py` dari cahyadsn/wilayah (MIT) | poligon disederhanakan hanya untuk uji titik |
| OpenStreetMap | 1 kueri Overpass (snapshot ODbL) | tidak ada pemindaian massal Nominatim/Overpass |
| Overture Maps Places | `overture_fetch.py` via DuckDB (CDLA-P 2.0) | saringan nama/kategori ketat; kategori bela diri lain masuk antrean tinjauan |
| Daftar tim (Surabaya) | `user_lists/*.json` | hanya nama/alamat; tanpa rating, ulasan, jam, telepon; Plus Code pendek didecode ke titik |
| Google Places API | `places_discover.py` (butuh kunci; berbayar; batas `--max-requests`) | belum dijalankan; ketentuan Google membatasi penyimpanan permanen |
| Google Maps (HTML) | **tidak** di-scrape | melanggar ketentuan & butuh menembus proteksi bot |

Presisi lokasi: `exact` (titik tempat) atau `regency` (penanda wilayah; tanpa petunjuk arah). Tidak ada koordinat tebakan.

## API (`/api/v1/directory`)
`GET /places` (bbox, zoom, near, filter; mode `clusters` bila >20 hasil & zoom<8), `GET /list`, `GET /places/{slug}`, `GET /facets`, `GET /stats`, `GET /heritage-areas`, `POST /submissions` (publik, rate limit 8/jam/IP, honeypot, skema ketat), `GET /submissions` & `POST /submissions/{id}/review` (kurator/admin). Kiriman tidak pernah terbit otomatis.

## DB
Migrasi `c4d8e2f6a1b3` (aditif): `directory_regions/organizations/places/place_sources/heritage_areas/import_jobs/place_history/submissions`. Indeks lat/lng, indeks unik dedup, `CHECK` koordinat dalam Indonesia. Impor `app.cli directory-import` idempoten, tidak menghapus: tempat yang hilang dari build disembunyikan (`publication_status=hidden`) dengan riwayat.

## Keterbatasan jujur
Cakupan 33/38 provinsi dan ±185/514 kab/kota (bukan jumlah seluruh perguruan). Sumber Overture sebagian dari halaman Meta dan bisa usang. Jadwal/kontak hampir kosong karena tidak ada sumber yang layak.
