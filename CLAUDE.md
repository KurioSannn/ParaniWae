# CLAUDE.md - SILATARA project instructions

## Project mission
Build SILATARA: a partner-led pencak silat heritage and learning platform. It is for cultural learning, safe beginner practice, documented knowledge transmission, and connection to real instructors - not combat optimization.

## Read before coding
- `PROJECT_CONTEXT.md`
- `PRD.md`
- `DESIGN.md`
- `AGENTS.md`
- `docs/TECHNICAL_ARCHITECTURE.md`
- `docs/AI_MOVEMENT_ASSESSMENT.md`
- `docs/PRIVACY_SAFETY_AND_ETHICS.md`
- `docs/RESEARCH_BRIEF.md` and `docs/COMPETITIVE_ANALYSIS.md`

## Non-negotiable rules
1. Inspect the current repository, existing code, tests, assets, and package manager before changing anything. Do not overwrite or delete unfamiliar work.
2. Treat proposed features and metrics as plans until code, tests, and evidence prove them. Never claim a feature works if it is a mock.
3. Do not invent partner names, cultural facts, instructor approvals, user-research results, testimonials, user counts, AI scores, or accuracy numbers.
4. Do not flatten regional styles into one universal movement standard. Every assessed movement requires a partner/style ID, reference version, instructor-approved rubric, and permission status.
5. Do not score low-quality or incomplete landmark input. Return `not_assessable` with a useful explanation.
6. AI is a practice aid, not a rank/belt certifier, combat assessor, safety authority, or replacement for an instructor.
7. MVP scope is one partner tradition and about 8-12 safe beginner solo movements chosen by that partner. Do not expand to sparring, weapons, throws, contact drills, acrobatics, or advanced techniques without explicit expert-supervised requirements.
8. Camera use must be opt-in, visible, stoppable at all times, and on-device by default. Never persist raw video by default.
9. Do not add tracking, analytics, or third-party services that collect camera frames or personal data without explicit necessity and disclosure.
10. Do not publish cultural material until source, attribution, permission, access level, and review status are recorded.
11. Use Bahasa Indonesia for the user-facing product by default.
12. Keep UI calm, premium, culturally grounded, accessible, and non-aggressive. Follow `DESIGN.md`; avoid generic AI-dashboard aesthetics.
13. Use tests and type checks. Do not disable or delete tests to make a build pass.
14. Make incremental, reversible changes. Ask before destructive operations, external publication, production database writes, or sending data to third parties.
15. Do not backdate or manipulate timestamps. BUDAYA GO! 2026 requires product availability by 31 March 2026; eligibility claims must be supported by contemporaneous evidence.

## Engineering workflow
1. `pwd`, inspect repository tree, `git status`, package manifests, and existing architecture.
2. Read source materials in `reference-materials/`; distinguish user evidence from desk research.
3. Write or update a concise implementation plan and acceptance checklist before broad edits.
4. Build a vertical slice first: one approved cultural item -> one lesson -> one movement -> camera/landmarks -> assessment -> result -> progress save.
5. Keep CV inference on the client when feasible. If processing blocks rendering, move it to a Worker or use a tested scheduling strategy.
6. Keep assessment logic pure/testable and separate from React UI.
7. Store rubric and reference versions with every result.
8. Run tests, lint, typecheck, and a manual browser/camera flow before reporting completion.

## Architecture defaults
Unless the existing repository dictates otherwise and the change is justified:
- Frontend: Next.js App Router + TypeScript.
- UI: Tailwind CSS with accessible primitives (for example, Radix-based components) and Lucide icons.
- Browser CV: `@mediapipe/tasks-vision` (Pose/Hand tasks); evaluate Holistic only if a clear need exists.
- Backend: Python FastAPI for application APIs and assessment persistence.
- Database: PostgreSQL with migrations.
- Object storage: S3-compatible, only for approved assets and user-consented uploads.
- Local development: Docker Compose where practical.

These are defaults, not permission to introduce unnecessary dependencies. Check current official docs and existing package constraints before choosing versions.

## Definition of done
A task is not complete until the relevant implementation, tests, error states, documentation, and verification are complete. Report what was built, what was tested, what was not tested, and any remaining blockers. Never claim a webcam/AI flow is verified when it was not run on a camera-capable browser/device.

## Source-of-truth hierarchy
1. Current explicit user direction.
2. Official BUDAYA GO! Juknis and included proposal template for competition requirements.
3. Approved partner documents and instructor validation for cultural content and movement rubrics.
4. Raw user research files for survey/interview claims.
5. Peer-reviewed research and official technical documentation for literature/technology.
6. Product hypotheses in this pack (must be tested).

When sources conflict, document the conflict; do not silently reconcile or fabricate.
