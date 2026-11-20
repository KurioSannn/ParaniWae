# AGENTS.md - Team and agent operating contract

This file provides cross-agent guidance. Claude Code-specific persistent instructions are in `CLAUDE.md`; specialist subagents are under `.claude/agents/`.

## Shared mission
Build SILATARA as a culturally grounded learning and preservation product. Technology must serve a partner-approved learning objective and must not override the knowledge holder's authority.

## Required roles

### Product owner
- Owns product scope, priority, acceptance criteria, and competition alignment.
- Decides what belongs in MVP and what remains future scope.
- Approves claims and public positioning.

### Cultural partner lead
- Coordinates with school/instructors/maestro.
- Obtains explicit permission and records provenance.
- Validates terminology, movement references, teaching sequence, correction rules, and access restrictions.
- Has authority to flag culturally inaccurate or sensitive content.

### UX/UI designer
- Owns user journeys, information architecture, visual system, interaction states, responsive behavior, and accessibility.
- Must distinguish real product functions from planned concepts.
- Must not invent partner logos, testimonials, statistics, or cultural material.

### Frontend engineer
- Owns web UI, camera lifecycle, browser inference integration, accessibility, and state management.
- Must stop camera tracks on unmount/error/stop and prevent duplicate inference loops.

### Computer-vision engineer
- Owns landmark processing, movement features, assessment pipeline, evaluation protocol, performance, and model limitations.
- Must not create or tune cultural standards without instructor-approved rubrics.

### Backend engineer
- Owns API contracts, authentication/authorization, persistence, partner/content workflows, audit logs, and data lifecycle.

### QA/research evaluator
- Owns reproducible test scenarios, device/camera matrix, learning study protocol, expert comparison, and regression testing.

## Delegation rules
- Delegate independent research, code review, accessibility audit, or test planning to specialist agents when the task is large enough.
- Do not delegate overlapping edits to multiple agents in the same files/feature branch.
- The primary agent integrates all findings and resolves conflicts.
- Cultural-domain reviewer can block publication of unvalidated material; QA can block a release if safety/privacy/camera states are missing.

## Evidence labels
Every major requirement/result must be classified as one of:
- `SOURCE-FACT`: present in official/user-provided source.
- `RESEARCH-FINDING`: supported by a cited paper, repository, or official source.
- `USER-REPORTED`: stated by founder but raw evidence not inspected.
- `PRODUCT-DECISION`: decision made for SILATARA.
- `HYPOTHESIS`: must be validated.
- `TARGET`: intended metric, not achieved result.

Never change a hypothesis or target into an achieved result without evidence.

## Cultural and data stewardship
- Preserve community attribution and consent.
- Respect restricted/sacred material; public access is not the default.
- Record partner-approved access scope: public, community-only, restricted.
- Avoid scraping/rehosting content without rights.
- Do not infer that one partner can authorize all styles or regional traditions.

## Safety
- Only approved solo beginner movements are eligible for home AI practice.
- Exclude sparring, opponent interaction, weapon techniques, throws, high-impact drills, and dangerous moves from unsupervised practice.
- Provide warm-up/safe-space guidance and stop/pain messaging.
- AI feedback must be framed as guidance, not formal assessment or medical advice.

## Collaboration protocol
Before starting a workstream, state the files to inspect/change and the acceptance criteria. After the workstream, report changed files, test results, assumptions, and unresolved issues. Keep an architecture decision record for any change to the chosen stack or data lifecycle.
