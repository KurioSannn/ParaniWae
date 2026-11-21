"""Penggerak load test (httpx, thread). Mengukur latensi (p50/p95/p99), throughput, error rate, query per request, koneksi DB.
Hasil NYATA dari run ini saja — tidak ada target yang dikarang. Jalankan lewat `make loadtest`."""

import json
import statistics
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099"
DURATION = float(sys.argv[2]) if len(sys.argv) > 2 else 20
CONC = int(sys.argv[3]) if len(sys.argv) > 3 else 20
D = json.load(open("/tmp/loadtest-seed.json"))
LEARN = [e for e in D["tokens"] if e.startswith("lt-l")]


def client(email):
    c = httpx.Client(base_url=BASE, timeout=30, headers={"X-CSRF-Token": D["csrf"][email]}, cookies={"silatara_session": D["tokens"][email]})
    return c


def timed(c, method, path, **kw):
    t0 = time.perf_counter()
    try:
        r = c.request(method, path, **kw)
        return r.status_code, (time.perf_counter() - t0) * 1000, int(r.headers.get("x-db-queries", 0))
    except Exception:  # noqa: BLE001
        return 0, (time.perf_counter() - t0) * 1000, 0


def scenario_runner(name, fn, workers, results, stop_at):
    def worker(i):
        c = client(LEARN[i % len(LEARN)]) if name not in ("program_detail", "cohort_listing", "analytics", "cohort_dashboard") else client("lt-ins@load.test")
        n = 0
        while time.perf_counter() < stop_at:
            results[name].append(fn(c, i, n))
            n += 1
        c.close()

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(worker, range(workers)))


S = {
    "session_validation": lambda c, i, n: timed(c, "GET", "/api/v1/auth/me"),
    "private_course_detail": lambda c, i, n: timed(c, "GET", f"/api/v1/courses/{D['course_slug']}"),
    "lesson_access": lambda c, i, n: timed(c, "GET", f"/api/v1/courses/{D['course_slug']}/lessons/{D['lesson_slugs'][n % len(D['lesson_slugs'])]}"),
    "learning_progress": lambda c, i, n: timed(c, "PUT", f"/api/v1/me/lessons/{D['lesson_ids'][n % len(D['lesson_ids'])]}/progress", json={"status": "in_progress"}),
    "practice_history": lambda c, i, n: timed(c, "GET", "/api/v1/me/practice-sessions?page_size=20"),
    "portal": lambda c, i, n: timed(c, "GET", "/api/v1/pilot/me/portal"),
    "program_detail": lambda c, i, n: timed(c, "GET", f"/api/v1/pilot/programs/{D['program_id']}"),
    "cohort_listing": lambda c, i, n: timed(c, "GET", f"/api/v1/pilot/cohorts/{D['cohort_ids'][n % 3]}"),
    "cohort_dashboard": lambda c, i, n: timed(c, "GET", f"/api/v1/pilot/cohorts/{D['cohort_ids'][n % 3]}/dashboard"),
    "analytics": lambda c, i, n: timed(c, "GET", f"/api/v1/pilot/programs/{D['program_id']}/analytics"),
}


def sample_connections(stop, out):
    import subprocess
    while not stop.is_set():
        r = subprocess.run(["python", "-c", "import psycopg,os;c=psycopg.connect(host=os.environ['POSTGRES_HOST'],user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD'],dbname=os.environ['POSTGRES_DB']);print(c.execute(\"select count(*) from pg_stat_activity where datname=current_database()\").fetchone()[0])"],
                           capture_output=True, text=True)
        if r.stdout.strip().isdigit():
            out.append(int(r.stdout.strip()))
        stop.wait(2)


def accept_run():
    """Penerimaan undangan: tiap undangan dipakai sekali oleh pengguna baru; laju diukur di konkurensi tetap."""
    res = []
    news = [e for e in D["tokens"] if e.startswith("lt-new")]
    pairs = list(zip(news, D["invites"], strict=False))

    def one(p):
        email, tok = p
        c = client(email)
        t0 = time.perf_counter()
        r = c.post("/api/v1/pilot/invitations/accept", json={"token": tok, "operational_ack": True})
        res.append((r.status_code, (time.perf_counter() - t0) * 1000, int(r.headers.get("x-db-queries", 0))))
        c.close()

    t0 = time.perf_counter()
    with ThreadPoolExecutor(min(CONC, 10)) as ex:
        list(ex.map(one, pairs))
    return res, time.perf_counter() - t0


def login_run(n=40):
    res = []
    for i in range(n):
        t0 = time.perf_counter()
        r = httpx.post(BASE + "/api/v1/auth/login", json={"email": f"lt-l{i}@load.test", "password": "sandi-load-test-123"}, timeout=30)
        res.append((r.status_code, (time.perf_counter() - t0) * 1000, int(r.headers.get("x-db-queries", 0))))
    return res


def summarize(rows, elapsed=None):
    lat = sorted(x[1] for x in rows)
    ok = [x for x in rows if 200 <= x[0] < 300]
    if not lat:
        return {}

    def pct(p):
        return round(lat[min(len(lat) - 1, int(len(lat) * p))], 1)

    codes = defaultdict(int)
    for x in rows:
        codes[x[0]] += 1
    return {"requests": len(rows), "ok": len(ok), "error_rate": round(1 - len(ok) / len(rows), 4), "status_codes": dict(codes),
            "p50_ms": pct(0.50), "p95_ms": pct(0.95), "p99_ms": pct(0.99), "max_ms": round(lat[-1], 1), "mean_ms": round(statistics.mean(lat), 1),
            "throughput_rps": round(len(rows) / (elapsed or DURATION), 1), "queries_per_request_avg": round(statistics.mean(x[2] for x in rows), 1),
            "queries_per_request_max": max(x[2] for x in rows)}


def main():
    conns, stop = [], threading.Event()
    th = threading.Thread(target=sample_connections, args=(stop, conns), daemon=True)
    th.start()
    report = {"base": BASE, "duration_s_per_scenario": DURATION, "concurrency": CONC, "learners": D["learners"], "scenarios": {}}
    for name, fn in S.items():
        results: dict = defaultdict(list)
        t0 = time.perf_counter()
        scenario_runner(name, fn, CONC, results, t0 + DURATION)
        report["scenarios"][name] = summarize(results[name], time.perf_counter() - t0)
        print(name, report["scenarios"][name], flush=True)
    rows, el = accept_run()
    report["scenarios"]["invitation_accept"] = summarize(rows, el)
    print("invitation_accept", report["scenarios"]["invitation_accept"], flush=True)
    report["scenarios"]["login_argon2"] = summarize(login_run(), None)
    print("login_argon2", report["scenarios"]["login_argon2"], flush=True)
    stop.set()
    report["db_connections"] = {"samples": len(conns), "max": max(conns) if conns else None, "avg": round(statistics.mean(conns), 1) if conns else None}
    json.dump(report, open("/tmp/loadtest-report.json", "w"), indent=1)
    print("\nDB connections:", report["db_connections"])


main()
