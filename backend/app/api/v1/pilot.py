from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, PageParams, auth_required
from app.core.db import get_db
from app.core.errors import ApiError
from app.core.netinfo import client_ip
from app.models import CohortInvitation, PilotCohort, PilotSurvey
from app.schemas import pilot as sc
from app.services import audit, ratelimit
from app.services import pilot as svc
from app.services import pilot_analytics as an
from app.services import studio_perm as perm

router = APIRouter(prefix="/pilot", tags=["pilot & impact"])
Authed = auth_required()


def _rid(r: Request):
    return getattr(r.state, "request_id", None)


def _manage(ctx: AuthContext):
    if ctx.user.role not in perm.STUDIO_ROLES:
        raise ApiError(403, "FORBIDDEN", "Hanya instruktur, kurator, atau admin.")


# ---------- program ----------
@router.get("/programs", summary="Program yang dapat saya kelola")
def list_programs(
    status: str | None = None,
    p: PageParams = Depends(),
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    return svc.list_programs(db, ctx.user, p.page, p.page_size, status)


@router.post("/programs", status_code=201, summary="Buat program (draf)")
def create_program(
    body: sc.ProgramCreate, request: Request, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)
):
    prog = svc.create_program(db, ctx.user, body, _rid(request))
    db.commit()
    return svc.program_out(db, ctx.user, prog, detail=True)


@router.get("/programs/{program_id}", summary="Detail program")
def get_program(program_id: str, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    _manage(ctx)
    return svc.program_out(db, ctx.user, svc.get_program(db, ctx.user, program_id), detail=True)


@router.patch("/programs/{program_id}", summary="Ubah program (draf)")
def patch_program(
    program_id: str,
    body: sc.ProgramPatch,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    prog = svc.get_program(db, ctx.user, program_id)
    svc.update_program(db, ctx.user, prog, body, _rid(request))
    db.commit()
    return svc.program_out(db, ctx.user, prog, detail=True)


@router.post("/programs/{program_id}/transition", summary="Lifecycle program")
def transition(
    program_id: str,
    body: sc.ProgramAction,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    prog = svc.get_program(db, ctx.user, program_id)
    svc.transition(db, ctx.user, prog, body, _rid(request))
    db.commit()
    return svc.program_out(db, ctx.user, prog, detail=True)


# ---------- cohort ----------
@router.post("/programs/{program_id}/cohorts", status_code=201, summary="Buat cohort")
def create_cohort(
    program_id: str,
    body: sc.CohortCreate,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    prog = svc.get_program(db, ctx.user, program_id)
    c = svc.create_cohort(db, ctx.user, prog, body, _rid(request))
    db.commit()
    return svc.cohort_out(db, c)


@router.get("/cohorts/{cohort_id}", summary="Detail cohort (pengelola)")
def get_cohort(cohort_id: str, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    _manage(ctx)
    c, prog = svc.get_cohort(db, ctx.user, cohort_id)
    return {
        **svc.cohort_out(db, c),
        "program": svc.program_out(db, ctx.user, prog),
        "members": svc.members_out(db, c),
        "invitations": [
            svc.invitation_out(i)
            for i in db.scalars(
                select(CohortInvitation)
                .where(CohortInvitation.cohort_id == c.id)
                .order_by(CohortInvitation.created_at.desc())
            )
        ],
    }


@router.patch("/cohorts/{cohort_id}", summary="Ubah cohort")
def patch_cohort(
    cohort_id: str,
    body: sc.CohortPatch,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    c, prog = svc.get_cohort(db, ctx.user, cohort_id)
    svc.update_cohort(db, ctx.user, c, prog, body, _rid(request))
    db.commit()
    return svc.cohort_out(db, c)


@router.post("/cohorts/{cohort_id}/status", summary="Buka/tutup/selesaikan cohort")
def cohort_status(
    cohort_id: str,
    body: sc.CohortStatus,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    c, prog = svc.get_cohort(db, ctx.user, cohort_id)
    svc.set_cohort_status(db, ctx.user, c, prog, body.status, _rid(request))
    db.commit()
    return svc.cohort_out(db, c)


@router.put("/cohorts/{cohort_id}/sessions", summary="Ganti jadwal cohort")
def put_sessions(
    cohort_id: str,
    body: sc.SessionsPut,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    c, _ = svc.get_cohort(db, ctx.user, cohort_id)
    svc.put_sessions(db, ctx.user, c, body, _rid(request))
    db.commit()
    return svc.cohort_out(db, c)


@router.delete("/cohorts/{cohort_id}/members/{user_id}", status_code=204, summary="Keluarkan peserta")
def remove_member(
    cohort_id: str, user_id: str, request: Request, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)
):
    _manage(ctx)
    c, _ = svc.get_cohort(db, ctx.user, cohort_id)
    svc.remove_member(db, ctx.user, c, user_id, _rid(request))
    db.commit()


# ---------- undangan ----------
@router.post("/cohorts/{cohort_id}/invitations", status_code=201, summary="Buat undangan (token ditampilkan sekali)")
def create_invitation(
    cohort_id: str,
    body: sc.InviteCreate,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    c, prog = svc.get_cohort(db, ctx.user, cohort_id)
    inv, raw = svc.create_invitation(db, ctx.user, c, prog, body, _rid(request))
    db.commit()
    return {
        **svc.invitation_out(inv),
        "token": raw,
        "token_note": "Token hanya ditampilkan sekali dan tidak dapat dilihat lagi.",
    }


@router.delete("/invitations/{invitation_id}", summary="Cabut undangan")
def revoke_invitation(
    invitation_id: str, request: Request, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)
):
    _manage(ctx)
    inv = db.get(CohortInvitation, perm.parse_id(invitation_id, "Undangan"))
    if not inv:
        raise ApiError(404, "NOT_FOUND", "Undangan tidak ditemukan.")
    svc.get_cohort(db, ctx.user, inv.cohort_id)
    svc.revoke_invitation(db, ctx.user, inv, _rid(request))
    db.commit()
    return svc.invitation_out(inv)


@router.get("/invitations/preview", summary="Pratinjau undangan (publik, tanpa data pribadi)")
def preview(request: Request, token: str = Query(..., min_length=20, max_length=200), db: Session = Depends(get_db)):
    ratelimit.hit(db, "invite:preview", client_ip(request), (60, 3600))
    return svc.preview(db, token)


@router.post("/invitations/accept", summary="Terima undangan")
def accept(body: sc.InviteAccept, request: Request, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    ratelimit.hit(db, "invite:accept", client_ip(request), (30, 3600))
    out = svc.accept(db, ctx.user, body, _rid(request))
    db.commit()
    return out


# ---------- portal pelajar ----------
@router.get("/me/portal", summary="Learner Pilot Portal")
def portal(ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    return svc.portal(db, ctx.user)


@router.get("/me/cohorts/{cohort_id}", summary="Cohort saya")
def my_cohort(cohort_id: str, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    return svc.my_cohort(db, ctx.user, cohort_id)


@router.delete("/me/cohorts/{cohort_id}", status_code=204, summary="Keluar dari cohort")
def leave(cohort_id: str, request: Request, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    svc.leave(db, ctx.user, cohort_id, _rid(request))
    db.commit()


@router.put("/me/programs/{program_id}/consents", summary="Ubah persetujuan opsional (riset/publikasi)")
def put_consents(
    program_id: str,
    body: sc.ConsentPut,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    out = svc.put_consents(db, ctx.user, program_id, body, _rid(request))
    db.commit()
    return out


# ---------- pengumuman ----------
@router.post("/programs/{program_id}/announcements", status_code=201, summary="Buat pengumuman (+ antre notifikasi)")
def announce(
    program_id: str,
    body: sc.AnnouncementIn,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    prog = svc.get_program(db, ctx.user, program_id)
    a = svc.announce(db, ctx.user, prog, body, _rid(request))
    db.commit()
    return {"id": a.id, "title": a.title, "delivery": svc.delivery_summary(db, a.id)}


@router.get("/programs/{program_id}/announcements", summary="Daftar pengumuman")
def announcements(program_id: str, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    _manage(ctx)
    prog = svc.get_program(db, ctx.user, program_id)
    return svc.announcements_out(db, prog.id)


# ---------- survei ----------
@router.get("/programs/{program_id}/surveys", summary="Survei program")
def surveys(program_id: str, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    _manage(ctx)
    prog = svc.get_program(db, ctx.user, program_id)
    from sqlalchemy import func

    from app.models import SurveyResponse

    return [
        svc.survey_out(
            s, db.scalar(select(func.count()).select_from(SurveyResponse).where(SurveyResponse.survey_id == s.id)) or 0
        )
        for s in db.scalars(
            select(PilotSurvey).where(PilotSurvey.program_id == prog.id).order_by(PilotSurvey.created_at)
        )
    ]


@router.post("/programs/{program_id}/surveys", status_code=201, summary="Buat survei khusus")
def create_survey(
    program_id: str,
    body: sc.SurveyCreate,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    prog = svc.get_program(db, ctx.user, program_id)
    s = svc.create_survey(
        db, ctx.user, prog, body.kind, body.title, [q.model_dump() for q in body.questions], _rid(request)
    )
    db.commit()
    return svc.survey_out(s)


@router.post("/programs/{program_id}/surveys/templates", status_code=201, summary="Buat survei dari templat draf")
def survey_template(
    program_id: str,
    body: sc.SurveyTemplate,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    prog = svc.get_program(db, ctx.user, program_id)
    s = svc.survey_from_template(db, ctx.user, prog, body.kind, _rid(request))
    db.commit()
    return svc.survey_out(s)


def _survey(db, ctx, survey_id) -> PilotSurvey:
    s = db.get(PilotSurvey, perm.parse_id(survey_id, "Survei"))
    if not s:
        raise ApiError(404, "NOT_FOUND", "Survei tidak ditemukan.")
    return s


@router.post("/surveys/{survey_id}/transition", summary="Buka/tutup survei")
def survey_transition(
    survey_id: str,
    body: sc.SurveyAction,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    _manage(ctx)
    s = _survey(db, ctx, survey_id)
    svc.get_program(db, ctx.user, s.program_id)
    svc.survey_action(db, ctx.user, s, body.action, _rid(request))
    db.commit()
    return svc.survey_out(s)


@router.get("/me/surveys", summary="Survei yang perlu saya isi")
def my_surveys(ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    return svc.pending_surveys(db, ctx.user)


@router.post("/surveys/{survey_id}/responses", status_code=201, summary="Kirim jawaban survei")
def submit(
    survey_id: str,
    body: sc.SurveySubmit,
    request: Request,
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    s = _survey(db, ctx, survey_id)
    svc.submit_survey(db, ctx.user, s, body, _rid(request))
    db.commit()
    return {"status": "submitted"}


# ---------- catatan instruktur ----------
@router.get("/cohorts/{cohort_id}/notes", summary="Catatan instruktur (bukan analytics)")
def notes(cohort_id: str, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    _manage(ctx)
    c, _ = svc.get_cohort(db, ctx.user, cohort_id)
    return svc.notes_out(db, c)


@router.post("/cohorts/{cohort_id}/notes", status_code=201, summary="Tambah catatan instruktur")
def add_note(
    cohort_id: str, body: sc.NoteIn, request: Request, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)
):
    _manage(ctx)
    c, _ = svc.get_cohort(db, ctx.user, cohort_id)
    svc.add_note(db, ctx.user, c, body, _rid(request))
    db.commit()
    return svc.notes_out(db, c)


# ---------- analytics ----------
def _scope(db, ctx, program_id, cohort_id):
    _manage(ctx)
    prog = svc.get_program(db, ctx.user, program_id)
    cid = perm.parse_id(cohort_id, "Cohort") if cohort_id else None
    role = svc.partner_role(db, ctx.user, prog.partner_id)
    if role not in {"admin", "manager"} and prog.responsible_user_id != ctx.user.id:
        # instruktur cohort: hanya cohort-nya
        mine = [
            c.id
            for c in db.scalars(
                select(PilotCohort).where(
                    PilotCohort.program_id == prog.id, PilotCohort.instructor_user_id == ctx.user.id
                )
            )
        ]
        if not mine or (cid and cid not in mine):
            raise ApiError(404, "NOT_FOUND", "Program tidak ditemukan.")
        cid = cid or (mine[0] if len(mine) == 1 else None)
        if cid is None:
            raise ApiError(422, "COHORT_REQUIRED", "Pilih cohort Anda untuk melihat analytics.")
    if cid and not db.scalar(select(PilotCohort.id).where(PilotCohort.id == cid, PilotCohort.program_id == prog.id)):
        raise ApiError(404, "NOT_FOUND", "Cohort tidak ditemukan.")
    return prog, cid


@router.get("/programs/{program_id}/analytics", summary="Analytics program (usage terpisah dari survei)")
def analytics(
    program_id: str,
    cohort_id: str | None = None,
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    prog, cid = _scope(db, ctx, program_id, cohort_id)
    return an.program_analytics(db, prog, cid, date_from, date_to, include_text=False)


@router.get("/cohorts/{cohort_id}/dashboard", summary="Instructor Cohort Dashboard")
def dashboard(cohort_id: str, ctx: AuthContext = Depends(Authed), db: Session = Depends(get_db)):
    _manage(ctx)
    c, prog = svc.get_cohort(db, ctx.user, cohort_id)
    return an.cohort_dashboard(db, c, prog)


@router.get("/programs/{program_id}/report.csv", summary="Ekspor CSV agregat (tanpa identitas)")
def report(
    program_id: str,
    request: Request,
    cohort_id: str | None = None,
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    ctx: AuthContext = Depends(Authed),
    db: Session = Depends(get_db),
):
    prog, cid = _scope(db, ctx, program_id, cohort_id)
    body = an.report_csv(db, prog, cid, date_from, date_to)
    audit.record(
        db,
        actor=ctx.user,
        action="pilot.report_export",
        entity_type="pilot_program",
        entity_id=prog.id,
        detail={"format": "csv"},
        request_id=_rid(request),
    )
    db.commit()
    return Response(
        body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="silatara-pilot-{prog.id}.csv"',
            "Cache-Control": "private, no-store",
        },
    )
