"""Uji alur end-to-end melalui origin FRONTEND (proxy Next), seperti browser.

Jalankan: make e2e-api  (stack E2E TERISOLASI: DB tmpfs, tidak menyentuh DB dev)
Hanya memakai stdlib. Membuat data uji unik (email acak, konten dengan nama 'E2E ...').
Memakai akun demo (APP_ENV=development) untuk peran kurator/admin.
"""

import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # agar `import app` bekerja

BASE = os.environ.get("E2E_BASE_URL", "http://frontend:3000")
DEMO_PW = os.environ.get("DEMO_USER_PASSWORD", "demo-sandi-12345")
results: list[tuple[bool, str]] = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


class Session:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), NoRedirect)

    def csrf(self):
        return next((c.value for c in self.jar if c.name == "silatara_csrf"), None)

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(BASE + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if method != "GET" and self.csrf():
            req.add_header("X-CSRF-Token", self.csrf())
        try:
            r = self.op.open(req, timeout=60)
            code, raw, loc = r.status, r.read(), None
        except urllib.error.HTTPError as e:
            code, raw, loc = e.code, e.read(), e.headers.get("Location")
        try:
            js = json.loads(raw)
        except Exception:
            js = None
        return code, js, raw.decode("utf-8", "replace"), loc


def check(ok, label):
    results.append((bool(ok), label))
    print(("PASS  " if ok else "FAIL  ") + label)


def verified_user(prefix="e2e"):
    """Daftar -> ambil token dari kotak surat dev -> verifikasi -> login. Mengembalikan Session."""
    import re
    s = Session()
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@uji.test"
    pw = "kata-sandi-e2e-123"
    code, js, *_ = s.call("POST", "/api/v1/auth/register", {"email": email, "password": pw, "display_name": "Pelajar E2E"})
    assert code == 202, (code, js)
    _, mails, *_ = s.call("GET", "/api/v1/dev/mailbox")
    token = re.search(r"token=([\w-]+)", next(m["body"] for m in mails if m["to"] == email))[1]
    code, js, *_ = s.call("POST", "/api/v1/auth/verify-email", {"token": token})
    assert code == 200, (code, js)
    code, js, *_ = s.call("POST", "/api/v1/auth/login", {"email": email, "password": pw})
    assert code == 200, (code, js)
    return s, email, js


def login(email):
    s = Session()
    code, js, *_ = s.call("POST", "/api/v1/auth/login", {"email": email, "password": DEMO_PW})
    assert code == 200, f"login {email} gagal: {code} {js}"
    return s


def main():
    # 1. Halaman publik, berisi data dari API+DB
    anon = Session()
    for path, needle in [("/", "Warisan Gerak"), ("/heritage", "[DEMO] Tradisi Contoh A"),
                         ("/heritage/demo-tradisi", "belum diverifikasi mitra"),
                         ("/community", "[DEMO] Perguruan Contoh A"),
                         ("/academy", "[DEMO] Kurikulum Contoh A"),
                         ("/academy/courses/demo-kurikulum-a", "Orientasi: Cara Memakai SILATARA")]:
        code, _, html, _ = anon.call("GET", path)
        check(code == 200 and needle in html, f"publik {path} berisi '{needle}'")
    code, _, html, _ = anon.call("GET", "/academy?q=Contoh+B&level=beginner&sort=-title")
    check("Kurikulum Contoh B" in html and "Kurikulum Contoh A" not in html, "filter/pencarian akademi bekerja")
    # konten non-publik tidak bocor
    for path in ["/heritage/demo-tradisi-draf", "/heritage/demo-tradisi-review",
                 "/academy/courses/demo-kurikulum-draf", "/community/demo-perguruan-draf"]:
        code, *_ = anon.call("GET", path)
        check(code == 404, f"{path} -> 404 (tidak bocor)")
    code, js, *_ = anon.call("GET", "/api/v1/courses?page_size=100")
    check(all("Draf" not in c["title"] for c in js["items"]), "API katalog tidak memuat draf")

    # 2. Proteksi halaman & endpoint
    for path in ["/app", "/app/progress", "/app/manage"]:
        code, _, _, loc = anon.call("GET", path)
        check(code == 307 and "/masuk" in (loc or ""), f"anonim {path} -> redirect ke /masuk")
    code, js, *_ = anon.call("GET", "/api/v1/me/progress")
    check(code == 401 and js["error"]["code"] == "UNAUTHENTICATED", "API privat tanpa sesi -> 401")

    # 3. Register (verifikasi email) -> belajar -> progres
    me = Session()
    email0 = f"enum-{uuid.uuid4().hex[:8]}@uji.test"
    r_new = me.call("POST", "/api/v1/auth/register", {"email": email0, "password": "kata-sandi-e2e-123", "display_name": "X Uji"})
    r_dup = Session().call("POST", "/api/v1/auth/register", {"email": email0, "password": "kata-sandi-e2e-123", "display_name": "X Uji"})
    check(r_new[0] == r_dup[0] == 202 and r_new[1] == r_dup[1], "registrasi: respons identik untuk email baru & sudah ada (anti-enumerasi)")
    check(not any(c.name == "silatara_session" for c in me.jar), "registrasi tidak memberi sesi sebelum verifikasi")
    code, js, *_ = me.call("POST", "/api/v1/auth/login", {"email": email0, "password": "kata-sandi-e2e-123"})
    check(code == 403 and js["error"]["code"] == "EMAIL_NOT_VERIFIED", "login sebelum verifikasi -> 403 EMAIL_NOT_VERIFIED")
    me, email, js = verified_user()
    check(js["user"]["role"] == "learner", "terverifikasi -> login -> learner + sesi")
    code, _, html, _ = me.call("GET", "/app")
    check(code == 200 and "Halo, Pelajar E2E" in html, "dasbor SSR menampilkan nama pengguna")
    code, _, html, _ = me.call("GET", "/app/courses/demo-kurikulum-a/lessons/demo-orientasi")
    check(code == 200 and "Ikuti kurikulum" in html, "pelajaran tanpa enrollment meminta daftar dulu")
    code, js, *_ = me.call("PUT", "/api/v1/me/lessons/" + "00000000-0000-0000-0000-000000000000" + "/progress", {"status": "completed"})
    check(code == 404, "menandai pelajaran fiktif -> 404")
    code, course, *_ = me.call("GET", "/api/v1/courses/demo-kurikulum-a")
    lessons = [(lesson["id"], lesson["slug"]) for m in course["modules"] for lesson in m["lessons"]]
    check(len(lessons) == 4 and course["enrollment"] is None, "kurikulum A memiliki 4 pelajaran, belum terdaftar")
    code, js, *_ = me.call("PUT", f"/api/v1/me/lessons/{lessons[0][0]}/progress", {"status": "completed"})
    check(code == 403 and js["error"]["code"] == "NOT_ENROLLED", "selesaikan tanpa enrollment -> 403 NOT_ENROLLED")
    code, js, *_ = me.call("POST", "/api/v1/courses/demo-kurikulum-a/enroll")
    check(code == 200 and js["progress"]["percent"] == 0, "enroll -> progres 0%")
    code, js, *_ = me.call("PUT", f"/api/v1/me/lessons/{lessons[0][0]}/progress", {"status": "completed"})
    check(code == 200 and js["enrollment"]["progress"]["percent"] == 25, "selesai 1/4 -> 25%")
    code, _, html, _ = me.call("GET", "/app/courses/demo-kurikulum-a/lessons/demo-keselamatan")
    check(code == 200 and "Kamera hanya menyala atas pilihan Anda" in html, "isi pelajaran 2 tampil (dari DB)")
    code, _, html, _ = me.call("GET", "/app/courses/demo-kurikulum-a/lessons/demo-referensi")
    check("Gerakan yang dipelajari" in html and "[DEMO] Gerakan Contoh 1" in html and "Bukan untuk dipraktikkan mandiri" in html,
          "pelajaran menampilkan referensi gerakan + mode latihan")
    for lid, _slug in lessons[1:]:
        code, js, *_ = me.call("PUT", f"/api/v1/me/lessons/{lid}/progress", {"status": "completed"})
    check(js["enrollment"]["progress"]["percent"] == 100 and js["enrollment"]["status"] == "completed",
          "4/4 selesai -> 100% & kurikulum selesai")
    code, _, html, _ = me.call("GET", "/app/progress")
    check(code == 200 and "100%" in html and "Kurikulum Contoh A" in html, "halaman progres menampilkan 100%")
    # 4. Otorisasi
    code, js, *_ = me.call("GET", "/api/v1/manage/courses")
    check(code == 403, "learner -> /manage 403")
    code, _, _, loc = me.call("GET", "/app/manage")
    check(code == 307 and "akses=ditolak" in (loc or ""), "learner /app/manage -> redirect ditolak")
    code, js, *_ = me.call("POST", "/api/v1/courses/demo-kurikulum-b/enroll")
    other, _, _ = verified_user("e2e2")
    code, js, *_ = other.call("GET", "/api/v1/me/progress")
    check(code == 200 and js["enrollments"] == [], "progres pengguna lain tidak terlihat (terisolasi)")
    code, js, *_ = Session().call("POST", "/api/v1/auth/logout")
    check(code == 401, "logout tanpa sesi ditolak (401)")

    # 5. Alur konten: kurator membuat -> admin menyetujui -> terbit -> tampil publik -> tarik
    cur = login("demo-kurator@silatara.test")
    adm = login("demo-admin@silatara.test")
    name = f"E2E Tradisi {uuid.uuid4().hex[:6]}"
    code, d, *_ = cur.call("POST", "/api/v1/manage/traditions",
                           {"name": name, "access_scope": "public", "source_citation": "Sumber uji E2E"})
    check(code == 201 and d["fields"]["status"] == "draft", "kurator membuat tradisi -> draf")
    tid, slug = d["fields"]["id"], d["fields"]["slug"]
    code, *_ = anon.call("GET", f"/heritage/{slug}")
    check(code == 404, "draf tidak tampil publik")
    code, d, *_ = cur.call("POST", f"/api/v1/manage/traditions/{tid}/transition", {"action": "submit"})
    check(code == 200 and d["fields"]["status"] == "pending_review", "ajukan review")
    code, *_ = anon.call("GET", f"/heritage/{slug}")
    check(code == 404, "pending_review tidak tampil publik")
    code, js, *_ = cur.call("POST", f"/api/v1/manage/traditions/{tid}/transition", {"action": "approve", "approval_evidence_ref": "x"})
    check(code == 403 and js["error"]["code"] == "SELF_APPROVAL", "kurator tidak dapat menyetujui kontennya sendiri")
    code, js, *_ = adm.call("POST", f"/api/v1/manage/traditions/{tid}/transition", {"action": "approve"})
    check(code == 422 and js["error"]["code"] == "EVIDENCE_REQUIRED", "persetujuan non-demo wajib bukti")
    code, d, *_ = adm.call("POST", f"/api/v1/manage/traditions/{tid}/transition", {"action": "approve", "approval_evidence_ref": "Berkas uji E2E (bukan persetujuan mitra sungguhan)"})
    check(code == 200 and d["fields"]["status"] == "verified", "admin menyetujui dengan bukti")
    code, *_ = anon.call("GET", f"/heritage/{slug}")
    check(code == 404, "verified (belum terbit) tidak tampil publik")
    code, d, *_ = adm.call("POST", f"/api/v1/manage/traditions/{tid}/transition", {"action": "publish"})
    check(code == 200 and d["fields"]["status"] == "published", "terbitkan")
    code, _, html, _ = anon.call("GET", f"/heritage/{slug}")
    check(code == 200 and name in html and "Terverifikasi oleh mitra" in html, "tampil publik dengan label verifikasi + penyetuju")
    code, _, html, _ = cur.call("GET", f"/app/manage/traditions/{tid}")
    check(code == 200 and "Riwayat audit" in html, "halaman kelola menampilkan riwayat audit")
    code, d, *_ = adm.call("POST", f"/api/v1/manage/traditions/{tid}/transition", {"action": "unpublish"})
    code2, *_ = anon.call("GET", f"/heritage/{slug}")
    check(code == 200 and code2 == 404, "tarik dari publik -> kembali 404")
    code, js, *_ = adm.call("GET", "/api/v1/admin/audit-logs?entity_type=traditions&page_size=50")
    acts = {a["action"] for a in js["items"] if a["entity_id"] == tid}
    check({"content.create", "content.submit", "content.approve", "content.publish", "content.unpublish"} <= acts, "jejak audit lengkap di DB")
    # soft-delete agar tidak mengotori katalog
    adm.call("DELETE", f"/api/v1/manage/traditions/{tid}")

    # 5b. Reset sandi: token sekali pakai, sesi lama dicabut
    import re
    rs, remail, _ = verified_user("rst")
    anon2 = Session()
    code, js, *_ = anon2.call("POST", "/api/v1/auth/password-reset/request", {"email": remail})
    code2, js2, *_ = anon2.call("POST", "/api/v1/auth/password-reset/request", {"email": f"tidak-ada-{uuid.uuid4().hex[:6]}@uji.test"})
    check(code == code2 == 202 and js == js2, "reset: respons identik untuk email terdaftar & tidak")
    _, mails, *_ = anon2.call("GET", "/api/v1/dev/mailbox")
    tok = re.search(r"token=([\w-]+)", next(m["body"] for m in mails if m["to"] == remail and "atur-ulang" in m["body"]))[1]
    code, *_ = anon2.call("POST", "/api/v1/auth/password-reset/confirm", {"token": tok, "new_password": "sandi-baru-e2e-panjang"})
    code_again, *_ = anon2.call("POST", "/api/v1/auth/password-reset/confirm", {"token": tok, "new_password": "sandi-lain-e2e-panjang"})
    code_old, *_ = rs.call("GET", "/api/v1/auth/me")
    check(code == 200 and code_again == 400 and code_old == 401, "reset: sekali pakai & sesi lama dicabut")

    # 5c. X-Forwarded-For palsu TIDAK boleh membuat kunci rate-limit sendiri (regresi temuan keamanan)
    import hashlib

    from sqlalchemy import text

    from app.core.db import get_engine
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM rate_limits WHERE key LIKE 'login:ip:%'"))
    for xff in (None, "6.6.6.6", "7.7.7.7, 8.8.8.8", "9.9.9.9"):
        req = urllib.request.Request(BASE + "/api/v1/auth/login", data=json.dumps({"email": "nobody@uji.test", "password": "x"}).encode(),
                                     headers={"Content-Type": "application/json", **({"X-Forwarded-For": xff} if xff else {})})
        try:
            urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError:
            pass
    with get_engine().connect() as conn:
        rows = dict(conn.execute(text("select key, count from rate_limits where key like 'login:ip:%'")).all())
    fake = {f"login:ip:{hashlib.sha256(ip.encode()).hexdigest()[:32]}" for ip in ("6.6.6.6", "7.7.7.7", "8.8.8.8", "9.9.9.9")}
    check(len(rows) == 1 and not (set(rows) & fake), "XFF palsu dari klien diabaikan (satu kunci rate-limit, bukan per IP palsu)")

    # 6. Logout mencabut sesi
    s = login("demo-pelajar@silatara.test")
    code, *_ = s.call("POST", "/api/v1/auth/logout")
    code2, *_ = s.call("GET", "/api/v1/auth/me")
    check(code == 204 and code2 == 401, "logout mencabut sesi")

    # 7. Aset MediaPipe tersaji dari origin sendiri
    for path in ["/mediapipe/wasm/vision_wasm_internal.wasm", "/mediapipe/models/pose_landmarker_lite.task", "/mediapipe/models/hand_landmarker.task"]:
        req = urllib.request.Request(BASE + path, method="HEAD")
        try:
            code = urllib.request.urlopen(req, timeout=30).status
        except urllib.error.HTTPError as e:
            code = e.code
        check(code == 200, f"aset MediaPipe {path} tersaji (200)")

    failed = [label for ok, label in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} pemeriksaan lulus")
    if failed:
        print("GAGAL:", *failed, sep="\n - ")
        sys.exit(1)


if __name__ == "__main__":
    main()
