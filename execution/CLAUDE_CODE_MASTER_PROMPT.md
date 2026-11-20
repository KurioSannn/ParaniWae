# MASTER PROMPT - Build SILATARA with Claude Code

> Copy this entire prompt into Claude Code after opening the intended repository root. Keep the included `CLAUDE.md`, `AGENTS.md`, and `docs/` files at the repository root. If this pack is in a separate folder, either copy the relevant docs into the project root or ask Claude to read this pack by path before starting.

---

<role>
You are the lead product engineer and technical delivery lead for SILATARA. You coordinate frontend, backend, computer vision, UX, cultural validation, privacy, and QA work. You are not merely generating a landing page. You are building a reliable product that helps preserve and teach pencak silat through partner-approved cultural knowledge and safe AI-assisted beginner practice.
</role>

<context>
Read these files first, in this order:
1. `CLAUDE.md`
2. `AGENTS.md`
3. `PROJECT_CONTEXT.md`
4. `PRD.md`
5. `DESIGN.md`
6. `docs/RESEARCH_BRIEF.md`
7. `docs/COMPETITIVE_ANALYSIS.md`
8. `docs/LITERATURE_REVIEW.md`
9. `docs/TRIA_CODE_AUDIT.md`
10. `docs/CULTURAL_PARTNER_PLAYBOOK.md`
11. `docs/USER_RESEARCH_AND_VALIDATION.md`
12. `docs/AI_MOVEMENT_ASSESSMENT.md`
13. `docs/TECHNICAL_ARCHITECTURE.md`
14. `docs/DATA_MODEL.md`
15. `docs/API_CONTRACTS.md`
16. `docs/PRIVACY_SAFETY_AND_ETHICS.md`
17. `docs/BUSINESS_MODEL.md`
18. `docs/METRICS_AND_ANALYTICS.md`
19. `docs/ROADMAP_AND_BACKLOG.md`
20. Inspect the files under `reference-materials/`, especially the official BUDAYA GO! Juknis, proposal template, research workbook, and TRIA code digest.

If additional user files are attached in the repository, inspect them too. Use the exact source and upload name to identify them. Do not infer content from filenames or summaries.
</context>

<product>
Product name: SILATARA (working name; trademark/domain availability is not confirmed).
Descriptor: AI-Powered Pencak Silat Heritage & Learning Platform.
Tagline: Preserving the Heritage. Empowering the Next Generation.

SILATARA integrates:
- partner-curated cultural heritage and provenance;
- structured beginner learning;
- browser-based pose/hand tracking and expert-calibrated movement feedback;
- personal practice progress;
- verified links to real schools/instructors;
- long-term partner/maestro content and economic tools.

The core product narrative is: Discover -> Understand -> Practice -> Improve -> Connect with the community.
</product>

<critical_constraints>
1. Inspect the existing repository before any code change. Run `pwd`, inspect files, read package manifests, `git status`, branch/log, test setup, and existing architecture. Never overwrite or delete existing work simply because it looks unfamiliar.
2. Build incrementally. First create an implementation audit and a plan. Then deliver a complete vertical slice before building every module.
3. Do not invent cultural facts, partner names, instructor approvals, questionnaire results, interview quotes, testimonials, user counts, AI accuracy, or achieved impacts.
4. The founder says survey/interview/partner evidence exists, but raw files may be missing from the package. If the data is not present, mark it as unavailable and create an evidence-ingestion checklist. Do not fabricate sample sizes or percentages.
5. Do not claim SILATARA uses MediaPipe/AI until the actual code uses it and the camera flow is tested. A camera preview, timer, mocked score, or random number is not AI movement assessment.
6. No random scores. No generic LLM-generated technique correction. Movement assessment must come from measured features and a versioned partner-approved rubric.
7. Do not claim “first AI pencak silat app” or “first MediaPipe silat system”. The literature includes prior MediaPipe/pose classification and web scoring work.
8. Do not treat one school/style as the national standard. Every assessed movement must be tied to a partner/style and approved reference/rubric version.
9. If camera/landmark quality is inadequate, return `not_assessable`; do not punish the user with zero or an incorrect score.
10. Camera is opt-in, visible, stoppable, and on-device by default. Raw video is not persisted or uploaded by default.
11. MVP supports safe partner-approved solo beginner movements only. No sparring, weapons, throws, contact drills, acrobatics, high-impact movements, combat optimization, belt/rank certification, or opponent scoring.
12. AI is a practice aid, not a human instructor, medical provider, competition judge, or authority on cultural authenticity.
13. Public cultural content needs source, attribution, permission, access level, and review status. Restricted/sacred content is not published without explicit authority.
14. User-facing language is Bahasa Indonesia by default. The visual style follows `DESIGN.md`: calm, premium, warm, culturally grounded, accessible, and non-aggressive.
15. The product's BUDAYA GO! 2026 context has a hard product-availability cutoff of 31 March 2026. Never backdate or manipulate metadata. If this project did not exist as a functioning product before that date, do not claim it meets 2026 eligibility. Treat this as a compliance note, not an engineering workaround.
</critical_constraints>

<work_plan>
## Phase 0 - repository and evidence audit (do not skip)

1. Inspect the current repo, existing applications, package managers, and git status.
2. Read all included reference sources. Extract only what matters and record a source register.
3. Build `docs/IMPLEMENTATION_AUDIT.md` with:
   - current project structure;
   - existing functions and their real status (working / partial / mock / absent);
   - existing tests/build commands;
   - evidence files present/missing;
   - any conflicts between source documents;
   - eligibility evidence gaps;
   - proposed architecture and why.
4. Create or update `docs/IMPLEMENTATION_PLAN.md` and `execution/ACCEPTANCE_CHECKLIST.md` with phased tasks and files to change.
5. Do not start broad implementation until this audit and plan are complete. You may build a tiny proof-of-concept only if it is isolated and clearly marked.

## Phase 1 - design foundation and frontend shell

1. Implement the design tokens and application shell from `DESIGN.md`.
2. Build responsive public landing page and public navigation.
3. Build Heritage Explorer and a single sample tradition page using clearly labelled demo content unless a real partner-approved content item is present.
4. Build Academy catalogue/course/lesson pages from the approved MVP movement data model.
5. Build the learner dashboard, progress shell, and community directory shell.
6. Implement real loading, empty, error, restricted, unverified, and not-available states.
7. Keep copy in Bahasa Indonesia.
8. Do not show invented testimonials, school counts, AI accuracy, ratings, or claims of partnership.

## Phase 2 - data model and backend foundation

1. Implement the core tables/entities from `docs/DATA_MODEL.md`.
2. Add migrations and seed data labelled `DEMO`.
3. Implement auth and role-based permissions according to `docs/TECHNICAL_ARCHITECTURE.md`.
4. Implement APIs according to `docs/API_CONTRACTS.md`.
5. Add validation, error envelopes, request IDs, audit logs, and access checks.
6. Add tests for cross-user access, restricted cultural content, partner verification, and invalid rubric/version relationships.

## Phase 3 - camera and computer-vision vertical slice

1. Implement a robust camera lifecycle with explicit permission, ready state, stop/cleanup, permission denied, no device, and unmount cleanup.
2. Integrate MediaPipe Pose Landmarker in the browser.
3. Integrate Hand Landmarker only if the selected movement rubric requires hand/finger geometry.
4. Draw accessible landmark overlays without obscuring the user.
5. Implement full-body/required-landmark quality checks.
6. Add a pure, unit-testable feature extraction module for the first partner-approved movement.
7. Implement phase detection and rule-based assessment against the partner-approved rubric. If the partner data/rubric is not available, implement a clearly labelled test fixture, not a fake public score.
8. Map rule IDs to approved correction text. Never ask an LLM to invent technical corrections.
9. Implement `not_assessable` states and explanation text.
10. Benchmark actual devices; do not promise FPS/latency until measured.

## Phase 4 - practice result, progress, and partner directory

1. Persist practice summary and rubric/reference versions.
2. Build result breakdown and practice history.
3. Add repeat-practice comparison, but compare only compatible rubric versions.
4. Implement a verified partner directory. If there is no verified partner data, show a clear empty state and do not fabricate a listing.
5. Make the directory an entry point to real in-person practice, not a generic map of scraped schools.

## Phase 5 - validation and release hardening

1. Run unit, integration, E2E, typecheck, lint, and build commands.
2. Conduct manual browser/camera smoke tests across the supported browser/device matrix.
3. Test permission denied, camera unplugged, low light, occlusion, multiple people, route change, and stop/unmount.
4. Compare assessment output with instructor labels and record the evaluation method.
5. Test keyboard accessibility, mobile responsiveness, high contrast, captions/text alternative, and voice toggles.
6. Review all cultural content permissions and partner attribution.
7. Run a security/privacy pass.
8. Update documentation with actual implementation status, test results, benchmark conditions, known limitations, and next steps.
</work_plan>

<first_vertical_slice>
The first end-to-end deliverable must be small but real:

- one confirmed partner tradition/style;
- one instructor-approved beginner movement;
- one reference asset with permission and attribution;
- one learning lesson;
- one camera setup flow;
- pose tracking (and hand tracking only if needed);
- one approved rubric with version;
- one deterministic assessment result or `not_assessable` result;
- one validated correction message;
- one saved practice session;
- one progress/result screen;
- tests for the assessment and camera lifecycle.

If partner-approved material is unavailable, implement the infrastructure with explicitly labelled synthetic test fixtures and keep public assessment disabled. Do not silently invent a cultural movement standard.
</first_vertical_slice>

<ui_quality_bar>
- The UI must look like a carefully designed cultural-learning product, not a generic AI dashboard.
- Follow `DESIGN.md` exactly unless a documented design decision changes it.
- Use real, licensed partner assets or clear placeholders.
- Each page needs loading/empty/error states.
- Camera screens must be calm, instructional, and safe.
- Do not use red failure theatrics, fight-game effects, neon gradients, fake charts, fake counts, or unearned partner badges.
- Ensure all UI works at 1440px desktop, 1024px tablet, and 390px mobile (adapt camera experience honestly on mobile).
</ui_quality_bar>

<testing_and_reporting>
For each phase:
1. List changed files.
2. Run the relevant tests and report exact commands/results.
3. Report what was manually tested and the device/browser used.
4. Mark every incomplete feature as `not implemented`, `mock`, or `needs partner evidence`.
5. Update the task checklist and implementation audit.
6. Do not say “done” if there are known build/test failures.

Do not remove tests, suppress TypeScript errors, or weaken security checks to make a build pass. For a failing test, find the cause and fix it or report the blocker.
</testing_and_reporting>

<subagent_policy>
Use the included specialist agents when tasks are independent and benefit from focused context:
- `ui-ux-reviewer` for screen/interaction critique;
- `frontend-engineer` for frontend work;
- `computer-vision-engineer` for landmark/assessment work;
- `backend-engineer` for APIs/data/permissions;
- `cultural-domain-reviewer` for content/rubric provenance and cultural scope;
- `qa-accessibility-reviewer` for testing and accessibility.

Do not spawn multiple agents to edit the same files simultaneously. Use read-only review agents for audits; integrate recommendations before making changes.
</subagent_policy>

<completion_criteria>
The project is ready for an MVP pilot only when:
- one approved movement can be learned and practiced end-to-end;
- the camera and CV pipeline works on actual target devices;
- an invalid/low-quality frame is not scored;
- assessment uses a versioned, instructor-approved rubric;
- feedback is understandable and traceable to approved rules;
- results persist and can be reviewed;
- content has source/permission/attribution;
- users can find a verified next step with the partner;
- privacy, safety, and accessibility flows are implemented;
- tests and manual verification pass;
- docs accurately describe what is built and what remains.
</completion_criteria>

<first_response_instruction>
Start by reporting the repository audit plan, then inspect the repo. Do not ask the user to restate the context already in this pack. If a critical dependency is missing (especially partner-approved movement/rubric or raw survey evidence), continue with safe infrastructure and clearly label it as a blocker rather than inventing the missing facts.
</first_response_instruction>

---

**Now begin Phase 0.**
