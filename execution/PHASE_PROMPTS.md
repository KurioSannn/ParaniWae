# Claude Code - Follow-up Phase Prompts

Use one prompt at a time. Each prompt assumes the master prompt and repository instructions are already loaded.

## Prompt A - Phase 0 repository/evidence audit

```text
Complete Phase 0 only. Inspect the repository, git state, package manager, source files, and all files under reference-materials/. Do not make broad implementation changes. Produce docs/IMPLEMENTATION_AUDIT.md and docs/IMPLEMENTATION_PLAN.md. Clearly separate SOURCE-FACT, RESEARCH-FINDING, USER-REPORTED, PRODUCT-DECISION, HYPOTHESIS, and TARGET. Identify missing questionnaire/interview/partner evidence and the BUDAYA GO! 31 March 2026 eligibility evidence gate. Summarize existing functions as working/partial/mock/absent. Finish with a proposed first vertical slice and acceptance checklist.
```

## Prompt B - Design and frontend shell

```text
Implement Phase 1 only. Use DESIGN.md and PRD.md. Build the design tokens, responsive app shell, landing page, Heritage Explorer/detail, Academy/course/lesson screens, learner dashboard, progress shell, and community directory shell. Use only clearly labelled demo content where no approved partner data exists. Make every empty/loading/error/restricted/unverified state. Do not implement fake AI. Run lint/typecheck/build and relevant UI tests. Report screenshots or browser verification results if your environment supports it.
```

## Prompt C - Backend/data foundation

```text
Implement Phase 2 only. Follow TECHNICAL_ARCHITECTURE.md, DATA_MODEL.md, API_CONTRACTS.md, PRIVACY_SAFETY_AND_ETHICS.md. Create migrations, role permissions, core models, APIs, validation, audit logging, and seed fixtures clearly marked DEMO. Add tests for authorization, cross-user access, restricted content, partner verification, permission revocation, and rubric version checks. Do not persist raw camera video. Run the backend test suite and report migrations/test results.
```

## Prompt D - Computer vision vertical slice

```text
Implement Phase 3 for one movement only. First verify that a real partner-approved movement reference and rubric exist. If absent, keep public AI practice disabled and build only a test fixture harness labelled DEMO. Integrate MediaPipe Pose Landmarker in the browser; add Hand Landmarker only when the selected rubric needs it. Build camera lifecycle, framing/visibility quality gate, worker/off-main-thread strategy if needed, deterministic feature extraction, phase handling, approved correction mapping, and not_assessable states. Never produce random scores or use an LLM to invent technical corrections. Add unit tests for coordinate/angle utilities and rubric evaluation. Benchmark actual devices and report conditions.
```

## Prompt E - Results, progress, community

```text
Implement Phase 4. Persist practice summaries with movement/rubric/reference/client-assessment versions. Build result breakdown, personal practice history, compatible-version comparison, and verified partner directory. If partner data is missing, show a thoughtful empty state; never invent schools, schedules, ratings, or contacts. Test access control and data ownership.
```

## Prompt F - Pilot QA and hardening

```text
Complete Phase 5. Run automated tests, typecheck, lint, build, accessibility checks, and manual camera tests. Include cases: permission denied, no camera, low light, partial body, hand occlusion, multiple people, browser route change, unmount, stop, model load error, offline/network failure. Confirm the app never scores not-assessable input. Audit content permissions, partner attribution, privacy and safety copy. Update the implementation audit and release checklist with exact results and remaining limitations.
```

## Prompt G - UX/UI review for the design teammate

```text
Act as a senior product designer. Review the implemented UI against DESIGN.md and PRD.md. Inspect all key routes and states. Report visual hierarchy, clarity, responsive layout, accessibility, cultural credibility, copy tone, empty/loading/error states, and whether the AI practice experience is understandable to a first-time user. Identify generic/AI-looking patterns, unlicensed/placeholder imagery problems, fake data, unclear permission flows, and any visual treatment that could shame beginners or glorify violence. Do not rewrite product strategy. Propose a prioritized, file-specific improvement list, then implement only the agreed fixes.
```
