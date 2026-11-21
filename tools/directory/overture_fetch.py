"""Ambil POI pencak silat dari Overture Maps Places (gratis, lisensi CDLA-Permissive-2.0 + atribusi) via DuckDB.

Hanya baris yang NAMA-nya cocok kata kunci pencak silat/perguruan, atau kategori martial arts, dalam kotak Indonesia.
Keluaran: research/pencak-silat/directory/raw/overture/places.json (diproses pipeline.py).
Pemakaian: python overture_fetch.py <release> <out.json>
"""
import json
import sys

import duckdb

release, out = sys.argv[1], sys.argv[2]
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2';")
NAME = (r"(silat|silek|pencak|penca\b|psht|setia hati|terate|pagar nusa|tapak suci|merpati putih|perisai (diri|putih)|ikspi|kera sakti|"
        r"\bipsi\b|paguron|paguruan|padepokan|kuntau|sasana|sanggar.*(silat|bela diri)|bela ?diri|cimande|cikalong|beksi|sera\b|"
        r"persinas|asad|satria muda|inti ombak|tunggal hati|pro patria|bakti negara|garuda putih|kalimasada|sinar putih)")
sql = f"""
SELECT id, names.primary AS name, taxonomy.primary AS category, basic_category AS basic_cat,
       addresses[1].freeform AS address, addresses[1].locality AS locality, addresses[1].region AS region,
       ST_Y(geometry) AS lat, ST_X(geometry) AS lng, confidence, operating_status,
       list_transform(sources, s -> s.dataset) AS datasets, list_transform(sources, s -> s.license) AS licenses
FROM read_parquet('s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*', hive_partitioning=1)
WHERE bbox.xmin BETWEEN 94.5 AND 141.5 AND bbox.ymin BETWEEN -11.5 AND 6.5
  AND (regexp_matches(lower(names.primary), '{NAME}')
       OR taxonomy.primary ILIKE '%martial%' OR taxonomy.primary ILIKE '%dojo%' OR taxonomy.primary ILIKE '%self_defense%' OR basic_category ILIKE '%martial%')
"""
con.execute("INSTALL spatial; LOAD spatial;")
rows = con.execute(sql).fetchall()
cols = [d[0] for d in con.description]
data = [dict(zip(cols, r)) for r in rows]
json.dump({"release": release, "count": len(data), "places": data}, open(out, "w"), ensure_ascii=False, default=str)
print(len(data))
