# CLAUDE.md - SILATARA project instructions

## Project mission
Build SILATARA: a public-first platform for knowledge, learning, and preservation of Indonesian pencak silat, for the
general public, students, culture enthusiasts, instructors, and prospective partner schools. Pencak silat knowledge
gathered from trustworthy sources is open to everyone. Partner schools can add their own official material, and that
material stays under their authority. The platform is about cultural learning, safe practice, documented knowledge
transmission, and connection to real instructors, not about combat optimization.

## Read before coding
- `PROJECT_CONTEXT.md`, `PRD.md`, `DESIGN.md`, `AGENTS.md`
- `docs/CONTENT_EDITORIAL_STANDARD.md` (content basis, publication paths, public copy)
- `docs/CONTENT_PROVENANCE.md`, `docs/MOVEMENT_CONTENT_STANDARD.md`, `docs/adr/0008-public-first-knowledge.md`
- `docs/TECHNICAL_ARCHITECTURE.md`, `docs/AI_MOVEMENT_ASSESSMENT.md`, `docs/PRIVACY_SAFETY_AND_ETHICS.md`

## Product rules (source of truth since 2026-11-21, owner directive; supersedes earlier partner-first rules)
1. SILATARA is a platform for knowledge, learning, and preservation of Indonesian pencak silat, oriented to the wider public.
2. Knowledge compiled from trustworthy sources (official documents, heritage inventories, academic studies, books, with
   page references) is **readable by the public without login**.
3. General learning material meant for the public must **never** require membership of a school or partner approval to read.
4. Processed research content belongs on the **main product pages** that fit it (`/heritage`, `/library`, `/academy`,
   `/community`). **Do not build a parallel "research" microsite.** Every content sprint integrates into the pages that
   already exist, with one canonical URL per content item.
5. Sources and provenance are always kept, and are shown as natural editorial references, not internal admin messages.
6. **Never fabricate** organisation identities, history, founders, lineages, techniques, philosophy, official curricula,
   partner names, instructor approvals, testimonials, user counts, AI scores, or accuracy numbers. If a source does not
   say it, leave it out or state the gap plainly ("Tidak dirinci dalam sumber").
7. Internal verification workflows stay in place, but they must not block access to general knowledge that is already
   source-backed. Distinguish three content bases (`content_basis`):
   - `source_backed`: general knowledge compiled by the SILATARA editorial team from open sources. It is published through
     editorial source review (reviewer identity, time, and evidence recorded). It **is not** a partner's official claim.
   - `official_curriculum`: a school's official curriculum or representation. It requires partner confirmation.
   - `partner_restricted`: internal or member-only material. It follows the owner's access limits.
8. The public website must not show narration about internal development status, test data, placeholders, seed status,
   approval workflows, or developer limitations.
9. Sample content (`is_demo`) and test accounts are isolated from the public experience (`EXPOSE_DEMO_DATA=false`
   outside tests/E2E). Never "convert" sample data into real data by deleting the `[DEMO]` label.
10. Login is only required for activities that truly need an account: enrollment, saving progress, practice history,
    camera Practice Studio, Studio/administration, and private pilot programs.

## Rules that must not be relaxed
11. Inspect the repository, code, tests, assets, and package manager before changing anything. Do not overwrite or delete
    unfamiliar work.
12. Treat proposed features and metrics as plans until code, tests, and evidence prove them. Never claim a mock works.
13. Do not flatten regional styles into one universal movement standard. Every *assessed* movement (AI scoring) requires a
    partner/style ID, reference version, instructor-approved rubric, and permission status.
14. Do not score low-quality or incomplete landmark input. Return `not_assessable` with a useful explanation.
15. AI is a practice aid, not a rank/belt certifier, combat assessor, safety authority, or replacement for an instructor.
16. Camera Practice Studio is limited to safe solo beginner movements with an approved rubric. No sparring, weapons,
    throws, contact drills, acrobatics, or advanced techniques without explicit expert-supervised requirements.
    Source-backed knowledge stays `practice_mode = not_for_practice` until an instructor approves a rubric.
17. Camera use must be opt-in, visible, stoppable at all times, and on-device by default. Never persist raw video by default.
18. Do not add tracking, analytics, or third-party services that collect camera frames or personal data without
    explicit necessity and disclosure.
19. Copyright: paraphrase, do not copy books, journals, or paid modules; do not reuse photos, illustrations, logos, or
    media without permission. Respect material that a source or school says must not be documented.
20. Private material stays private: partner-restricted content, licensed media, consent documents, and private pilot
    programs keep their access checks. Never grant edit or publish rights to anonymous users or learners.
21. Use Bahasa Indonesia for the user-facing product by default.
22. Keep the UI calm, premium, culturally grounded, accessible, and non-aggressive. Follow `DESIGN.md`. Public copy reads
    like editorial writing for people, not developer documentation.
23. Use tests and type checks. Do not disable or delete tests to make a build pass.
24. Make incremental, reversible changes. Ask before destructive operations, external publication, production database
    writes, or sending data to third parties. Back up the dev DB before migrations or bulk data changes. Never run
    `docker compose down -v`.
25. Do not backdate or manipulate timestamps. BUDAYA GO! 2026 requires product availability by 31 March 2026;
    eligibility claims must be supported by contemporaneous evidence.

## Engineering workflow
1. `pwd`, inspect repository tree, `git status`, package manifests, and existing architecture.
2. Read `research/` and `content/` in full before writing content features. Distinguish user evidence from desk research.
3. Write or update a concise plan and acceptance checklist before broad edits.
4. Content work: files in `content/` and `research/` are the single source of truth, then validate
   (`make content-validate`), then import (`make content-import`), then show on the main pages. Verify as an anonymous
   visitor and as a logged-in user, and run the link checker (`e2e-browser/scripts/link-check.mjs`).
5. Keep CV inference on the client when feasible; assessment logic pure/testable and separate from React UI.
6. Store rubric and reference versions with every assessment result.
7. Run tests, lint, typecheck, production build, and a manual browser flow before reporting completion.

## Architecture defaults
Next.js App Router + TypeScript, Tailwind CSS with accessible primitives and Lucide icons, `@mediapipe/tasks-vision`,
Python FastAPI, PostgreSQL with migrations, S3-compatible storage only for approved assets and consented uploads,
Docker Compose for local development. These are defaults, not permission to add unnecessary dependencies.

## Definition of done
A task is not complete until implementation, tests, error states, documentation, and verification are complete. Report
what was built, what was tested, what was not tested, and remaining blockers. Never claim a webcam/AI flow is verified
without running it on a camera-capable browser/device.

## Source-of-truth hierarchy
1. Current explicit user direction.
2. Official BUDAYA GO! Juknis and proposal template for competition requirements.
3. Approved partner documents and instructor validation for a school's official content and assessment rubrics.
4. Official heritage records (UNESCO, the WBTb inventory), academic publications, and books with clear publishers, for
   source-backed public knowledge.
5. Raw user research files for survey/interview claims.
6. Product hypotheses in this pack (must be tested).

When sources conflict, document the conflict; do not silently reconcile or fabricate.
