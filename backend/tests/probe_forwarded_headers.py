"""Probe BLACK-BOX untuk topologi reverse-proxy NYATA: apakah X-Forwarded-For palsu dari klien dapat melewati rate limit?

Jalankan terhadap lingkungan yang ingin diuji (staging/produksi), BUKAN DB dev bersama (probe ini menghabiskan batas login):
    python backend/tests/probe_forwarded_headers.py https://staging.contoh.id [jumlah=45]

Cara kerja: kirim N login gagal ke email acak, tiap request dengan X-Forwarded-For ACAK. Bila batas login/IP berlaku
per klien sebenarnya, respons 429 akan muncul setelah batas terlampaui MESKIPUN XFF berganti-ganti.
  - 429 muncul          -> XFF palsu TIDAK menghindari batas (lulus untuk probe ini)
  - 429 tidak pernah     -> XFF palsu dipercaya (GAGAL: pemalsuan header dapat melewati rate limit)
Probe ini tidak membuktikan topologi benar sepenuhnya (mis. proxy yang menambah, bukan menimpa, XFF tetap perlu ditinjau).
"""
import json
import random
import sys
import urllib.error
import urllib.request
import uuid

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:3000"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 45
hit429 = None
for i in range(1, n + 1):
    fake = ".".join(str(random.randint(1, 254)) for _ in range(4))
    req = urllib.request.Request(
        f"{base}/api/v1/auth/login",
        data=json.dumps({"email": f"probe-{uuid.uuid4().hex[:8]}@probe.invalid", "password": "x"}).encode(),
        headers={"Content-Type": "application/json", "X-Forwarded-For": fake},
    )
    try:
        urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            hit429 = i
            break
print(f"429 pertama pada request ke-{hit429}" if hit429 else f"TIDAK ADA 429 setelah {n} request dengan XFF acak")
print("HASIL:", "LULUS (XFF palsu tidak melewati batas)" if hit429 else "GAGAL (XFF palsu mungkin dipercaya, atau batas > N)")
sys.exit(0 if hit429 else 1)
