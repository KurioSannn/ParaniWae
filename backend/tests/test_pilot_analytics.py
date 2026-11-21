"""Learning analytics Pilot: angka harus sama dengan data sumber; privasi k-anonimitas; CSV tanpa identitas."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.models import CohortMember, LessonProgress, PartnerMember, PracticeSession
from tests.factories import make_user
from tests.test_pilot import (  # noqa: F401
    accept,
    api,
    approve_and_open,
    as_,
    invite,
    learner,
    mk_cohort,
    mk_program,
    ok,
    w,
)


def build(w, n, **cohort_over):
    p = mk_program(w)
    c = mk_cohort(w, p["id"], capacity=50, **cohort_over)
    approve_and_open(w, p["id"], c["id"])
    users = []
    for _ in range(n):
        u = learner(w.db)
        ok(accept(w, u, invite(w, c["id"])["token"]))
        users.append(u)
    as_(w.client, w.ins)
    return p, c, users


def progress(w, user, lesson, status):
    from sqlalchemy import select

    from app.models import Enrollment

    enr = w.db.scalar(select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.course_id == w.course.id))
    now = datetime.now(UTC)
    w.db.add(
        LessonProgress(
            user_id=user.id,
            enrollment_id=enr.id,
            course_id=w.course.id,
            lesson_id=lesson.id,
            status=status,
            started_at=now,
            completed_at=now if status == "completed" else None,
        )
    )
    w.db.flush()


def practice(w, user, lesson, status="completed", ms=120_000):
    now = datetime.now(UTC)
    w.db.add(
        PracticeSession(
            user_id=user.id,
            lesson_id=lesson.id,
            status=status,
            started_at=now - timedelta(minutes=5),
            ended_at=now,
            active_duration_ms=ms,
            paused_duration_ms=0,
            model_version="uji",
        )
    )
    w.db.flush()


def test_usage_metrics_match_source_data(w, db):
    p, c, us = build(w, 5)
    L = w.world["lessons"]
    for lesson in L:
        progress(w, us[0], lesson, "completed")
    progress(w, us[1], L[0], "completed")
    progress(w, us[2], L[0], "in_progress")
    practice(w, us[0], L[0], "completed", 120_000)
    practice(w, us[1], L[0], "abandoned", 0)
    db.execute(text("update cohort_members set joined_at = now() - interval '1 day'"))  # now() transaksi uji membeku
    db.expire_all()
    a = ok(api(w.client, "get", f"/programs/{p['id']}/analytics"))
    u = a["usage"]["cohorts"][0]
    assert u["active_members"] == 5 and u["lessons_total"] == 3 and u["suppressed"] is False
    assert u["lessons_completed"] == 4 and u["completion_rate"] == round(4 / 15, 4)  # selesai / (anggota × pelajaran)
    assert u["active_participants"] == 3 and u["active_rate"] == 0.6  # progres ATAU sesi latihan
    assert (
        u["practice"]["sessions"] == 2
        and u["practice"]["by_status"]["completed"] == 1
        and u["practice"]["by_status"]["abandoned"] == 1
    )
    assert u["practice"]["active_minutes"] == 2.0 and u["practice"]["sessions_per_active_participant"] == round(
        2 / 3, 2
    )
    ret = a["usage"]["retention"][0]
    assert ret["weeks"][0] == {"week": 1, "active": 3, "rate": 0.6}
    assert a["enrollment"]["active_total"] == 5 and a["enrollment"]["invitations"]["accepted"] == 5
    assert "bukan penguasaan teknik" in a["disclaimer"]
    # filter periode: di luar jendela -> 0 penyelesaian
    long_ago = ok(
        api(w.client, "get", f"/programs/{p['id']}/analytics", params={"from": "2020-01-01", "to": "2020-01-31"})
    )
    assert (
        long_ago["usage"]["cohorts"][0]["lessons_completed"] == 0
        and long_ago["usage"]["cohorts"][0]["active_participants"] == 0
    )


def test_small_groups_are_suppressed(w, db):
    p, c, us = build(w, 4)  # < K=5
    progress(w, us[0], w.world["lessons"][0], "completed")
    a = ok(api(w.client, "get", f"/programs/{p['id']}/analytics"))
    u = a["usage"]["cohorts"][0]
    assert (
        u["suppressed"] is True
        and u["completion_rate"] is None
        and u["practice"] is None
        and "Disembunyikan" in u["note"]
    )
    assert a["usage"]["retention"][0]["suppressed"] is True and a["consent"]["research_aggregate"] is None
    csvtxt = w.client.get(f"/api/v1/pilot/programs/{p['id']}/report.csv").text
    assert "DISEMBUNYIKAN" in csvtxt and "lesson_completion_rate" not in csvtxt


def test_survey_aggregates_response_rate_and_suppression(w, db):
    p, c, us = build(w, 6)
    s = ok(api(w.client, "post", f"/programs/{p['id']}/surveys/templates", json={"kind": "endline"}), 201)
    ok(api(w.client, "post", f"/surveys/{s['id']}/transition", json={"action": "open"}))

    def answer(u, rating):
        as_(w.client, u)
        ok(
            api(
                w.client,
                "post",
                f"/surveys/{s['id']}/responses",
                json={
                    "answers": {
                        "pengalaman": "Beberapa kali",
                        "percaya_diri": rating,
                        "akses_instruktur": "Cukup mudah",
                        "catatan": f"komentar {rating}",
                    }
                },
            ),
            201,
        )

    for u, r in zip(us[:4], (5, 4, 4, 3), strict=True):
        answer(u, r)
    as_(w.client, w.ins)
    sv = ok(api(w.client, "get", f"/programs/{p['id']}/analytics"))["surveys"][0]
    assert (
        sv["responses"] == 4
        and sv["response_rate"] == round(4 / 6, 4)
        and sv["suppressed"] is True
        and sv["questions"] == []
    )
    answer(us[4], 2)
    as_(w.client, w.ins)
    sv = ok(api(w.client, "get", f"/programs/{p['id']}/analytics"))["surveys"][0]
    assert sv["suppressed"] is False and sv["responses"] == 5 and sv["response_rate"] == round(5 / 6, 4)
    q = {x["id"]: x for x in sv["questions"]}
    assert q["percaya_diri"]["mean"] == round((5 + 4 + 4 + 3 + 2) / 5, 2)
    assert q["percaya_diri"]["distribution"] == {"1": 0, "2": 1, "3": 1, "4": 2, "5": 1}
    assert (
        q["pengalaman"]["distribution"]["Beberapa kali"] == 5 and "texts" not in q["catatan"]
    )  # teks terbuka tidak di analytics umum
    assert "komentar" not in w.client.get(f"/api/v1/pilot/programs/{p['id']}/report.csv").text


def test_cohort_dashboard_flags_attention_with_stated_thresholds(w, db):
    p, c, us = build(w, 4)
    L = w.world["lessons"]
    progress(w, us[0], L[0], "completed")
    progress(w, us[1], L[0], "in_progress")
    db.execute(
        text("update cohort_members set joined_at = now() - interval '5 days' where user_id = :u"), {"u": us[2].id}
    )
    db.execute(
        text("update lesson_progress set updated_at = now() - interval '9 days' where user_id = :u"), {"u": us[1].id}
    )
    db.expire_all()
    d = ok(api(w.client, "get", f"/cohorts/{c['id']}/dashboard"))
    by = {r["name"]: r for r in d["participants"]}
    rows = {p_["user_id"]: p_ for p_ in d["participants"]}
    assert d["thresholds"] == {"no_start_days": 3, "inactive_days": 7}
    assert d["summary"]["members"] == 4 and d["summary"]["not_started"] == 2
    assert rows[str(us[2].id)]["needs_attention"] and "belum memulai" in rows[str(us[2].id)]["attention_reasons"][0]
    assert rows[str(us[1].id)]["needs_attention"] and "tanpa aktivitas" in rows[str(us[1].id)]["attention_reasons"][0]
    assert not rows[str(us[3].id)]["needs_attention"]  # baru bergabung (<3 hari)
    assert rows[str(us[0].id)]["lessons_completed"] == 1 and rows[str(us[0].id)]["completion"] == round(1 / 3, 4)
    assert d["summary"]["needs_attention"] == 2 and by and "bukan penguasaan" in d["disclaimer"]


def test_csv_is_aggregate_only_and_blocks_formula_injection(w, db):
    p, c, us = build(w, 5)
    other = mk_cohort(w, p["id"], name='=HYPERLINK("http://x")', capacity=5)
    r = w.client.get(f"/api/v1/pilot/programs/{p['id']}/report.csv")
    assert (
        r.status_code == 200
        and r.headers["content-type"].startswith("text/csv")
        and r.headers["cache-control"] == "private, no-store"
    )
    body = r.text
    for u in us:
        assert u.email not in body and u.display_name not in body
    assert "'=HYPERLINK" in body and "\n=HYPERLINK" not in body and ",=HYPERLINK" not in body
    assert body.splitlines()[3] == "group,metric,cohort,value,n,note"
    from sqlalchemy import select

    from app.models import AuditLog

    assert db.scalar(select(AuditLog.id).where(AuditLog.action == "pilot.report_export", AuditLog.entity_id == p["id"]))
    _ = other


def test_analytics_access_control(w, db):
    p, c, us = build(w, 5)
    ins2 = make_user(db, "instructor")
    db.add(PartnerMember(partner_id=w.partner.id, user_id=ins2.id, role="instructor"))
    db.flush()
    c2 = mk_cohort(w, p["id"], instructor_user_id=str(ins2.id))
    as_(w.client, ins2)
    a = ok(api(w.client, "get", f"/programs/{p['id']}/analytics"))
    assert [x["cohort_id"] for x in a["usage"]["cohorts"]] == [c2["id"]]  # hanya cohort-nya
    assert api(w.client, "get", f"/programs/{p['id']}/analytics", params={"cohort_id": c["id"]}).status_code == 404
    assert api(w.client, "get", f"/cohorts/{c['id']}/dashboard").status_code == 404
    as_(w.client, w.other_ins)
    assert api(w.client, "get", f"/programs/{p['id']}/analytics").status_code == 404
    as_(w.client, us[0])
    assert api(w.client, "get", f"/programs/{p['id']}/analytics").status_code == 403
    _ = CohortMember
