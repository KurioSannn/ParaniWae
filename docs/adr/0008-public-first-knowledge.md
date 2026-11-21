# ADR-0008: Public-first knowledge and the end of the research microsite

- Status: accepted (product owner directive, 2026-11-21). Replaces ADR-0007 (the `/riset` microsite) and amends
  ADR-0006 (the editorial partner now serves only as the technical owner of `source_backed` rows).
- Date: 2026-11-21

## Context
The research results (38 provinces, 80 entities, 43 movements, 23 animations, 2 courses / 16 lessons, 34 sources)
were split off into `/riset`. Meanwhile the main pages showed `[DEMO]` content, "tahap pengembangan" copy, and
required logins or verified partners to read general material.

## Decision
1. **Content basis** (`content_basis` on traditions, movements, movement_documents, courses, lessons; migration
   `b8e4f1c2d7a9`). The default for existing rows is `official_curriculum`.
   - `source_backed`: published through editorial source review. Required: an editorial reviewer that is not a demo
     account (`approved_by`, `curator_reviewed_by`), a timestamp, and `approval_evidence_ref`. Partner confirmation is
     **not** required, and the content is never presented as a school's official material.
   - `official_curriculum` and `partner_restricted`: the old rules stay in force (partner confirmation, partner
     verified and publicly listed).
2. **Public visibility**: `visibility.movement_ok` and `course_public_ok` accept published `source_backed` content
   without a verified partner. Published lessons of public courses can be read anonymously
   (`GET /courses/{slug}/lessons/{lesson}` uses `optional_auth`). Private pilot courses stay 404 for anonymous visitors.
3. **Main pages**: `/heritage`, `/library`, `/academy`, `/community` render public knowledge from the same files as the
   importer (`/api/v1/research/*`, read-only), merged with partners' official content from the DB without duplicates.
   `/riset/*` returns a 308 redirect to the canonical URLs.
4. **Demo isolation**: dev compose sets `EXPOSE_DEMO_DATA=false`. Tests set their own fixtures. Demo login remains for
   development only (`DEMO_LOGIN_ENABLED`).
5. **Practice safety does not change**: `source_backed` content stays `practice_mode=not_for_practice` and
   `assessment_enabled=false`.

## Consequences
- Visitors can read and learn without an account. Login adds progress and practice tracking.
- DB publication (`make content-import X=1` with `--publish --operator <editor>`) requires a **real** editorial account.
  At this ADR's date the dev DB has no non-demo admin or curator account, so creating one is the owner's decision.
  Until then the public pages read from the content files, and enrollment and progress for the knowledge courses stay
  off (the course pages already handle that state).
- Risk: material that has not been confirmed by a school can be read publicly. Mitigations: every claim is referenced
  per page; there are no official claims, no unlicensed media, and no personal contacts; techniques that a source says
  must not be documented are not described.
