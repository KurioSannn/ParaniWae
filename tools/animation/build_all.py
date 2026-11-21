"""Bangun semua animasi + halaman pratinjau (alat pengembangan, di luar frontend).

Pemakaian:
    python3 tools/animation/build_all.py [content/pencak-silat/animations]
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import silat_anim as sa  # noqa: E402


def preview_html(root: Path, rows: list[dict]) -> str:
    cards = []
    for r in rows:
        mid = html.escape(r["movement_id"])
        if r["status"] == "generated":
            body = (
                f'<img src="{mid}/animation.svg" width="360" height="440" alt="Animasi {html.escape(r["title"])}">'
                f'<p class="meta">{r["duration_ms"]} ms · {r["view"]} · {r["svg_bytes"]} byte</p>'
            )
        else:
            body = f'<div class="todo"><strong>needs_reference</strong><p>{html.escape(r["needs"])}</p></div>'
        cards.append(f'<figure><figcaption><code>{mid}</code><br>{html.escape(r["title"])}</figcaption>{body}</figure>')
    return (
        "<!doctype html><html lang=\"id\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Pratinjau Animasi Gerak</title><style>"
        ":root{--bg:#F6F2E9;--card:#FCFBF7;--ink:#17231F;--muted:#52605A;--line:#E4E1D8;--warn:#A95743}"
        "body{margin:0;padding:16px;background:var(--bg);color:var(--ink);font-family:system-ui,sans-serif}"
        "h1{font-size:20px;margin:0 0 4px}p.lead{color:var(--muted);max-width:70ch}"
        "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}"
        "figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}"
        "figcaption{font-size:13px;margin-bottom:8px}img{width:100%;height:auto;display:block}"
        ".meta{font-size:11px;color:var(--muted)}.todo{border:1px dashed var(--warn);border-radius:8px;padding:12px;font-size:13px}"
        "</style></head><body><h1>Pratinjau animasi gerak (alat pengembangan)</h1>"
        "<p class=\"lead\">Semua animasi adalah interpretasi visual editorial atas dokumentasi tertulis dan <strong>belum divalidasi instruktur</strong>. "
        "Halaman ini bukan bagian aplikasi frontend.</p><main>"
        + "".join(cards)
        + "</main></body></html>\n"
    )


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path("content/pencak-silat/animations")
    rig = Path(__file__).resolve().parent / "rig.json"
    rows, failed = [], 0
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        spec = json.loads((d / "keyframes.json").read_text())
        if spec.get("animation_status") == "generated":
            try:
                man = sa.build(d, rig)
            except sa.AnimationError as e:
                print("GAGAL", e)
                failed += 1
                continue
            rows.append({"movement_id": spec["movement_id"], "title": spec["title"], "status": "generated", **man})
            print(f"OK   {spec['animation_id']}  {man['duration_ms']}ms  {man['svg_bytes']}B")
        else:
            rows.append({"movement_id": spec["movement_id"], "title": spec["title"], "status": "needs_reference", "needs": spec.get("needs", "")})
            print(f"SKIP {spec['movement_id']} (needs_reference)")
    (root / "index.html").write_text(preview_html(root, rows))
    print(f"{sum(r['status'] == 'generated' for r in rows)} animasi dibuat, {sum(r['status'] != 'generated' for r in rows)} needs_reference, {failed} gagal")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
