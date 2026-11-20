# SILATARA - Release Acceptance Checklist

## Product and cultural validity
- [ ] One anchor partner and the represented tradition/style are documented.
- [ ] Partner's authority/scope to approve the content is recorded.
- [ ] Movement names, phases, terminology, and cultural context are validated.
- [ ] Every movement assessment rubric has an approved version and instructor.
- [ ] Each asset has source, attribution, permission/license, access scope, and review date.
- [ ] No content is represented as national/universal if it is specific to one school/style.

## Eligibility and claims
- [ ] No false claim of BUDAYA GO! 2026 eligibility.
- [ ] Any claim of product availability by 31 March 2026 has contemporaneous evidence.
- [ ] Actual features are separated from planned features.
- [ ] No invented partner names, stats, testimonials, user counts, or AI accuracy claims.

## UX and content
- [ ] Landing page explains cultural learning, AI role, and limitations.
- [ ] Heritage pages show source/attribution and validation status.
- [ ] Academy content has objectives, phases, safety, and instructor reference.
- [ ] Camera permission is requested only after user action.
- [ ] Practice UI includes all camera and inference states.
- [ ] Feedback language is constructive, non-shaming, and Indonesian-first.
- [ ] Text is available for all voice feedback.
- [ ] Community directory contains only verified, consented entries.
- [ ] Responsive layout tested at desktop, tablet, and mobile sizes.

## Camera and AI
- [ ] Camera starts only after explicit action.
- [ ] All media tracks stop on stop, route change, unmount, logout, and error.
- [ ] Model load/error states are clear.
- [ ] Landmark quality gate works.
- [ ] Insufficient input returns `not_assessable`, not zero score.
- [ ] Supported movement only can be assessed.
- [ ] Assessment uses a versioned partner-approved rubric.
- [ ] Corrections reference approved rule IDs.
- [ ] No random/fake scores or generic AI-generated technique corrections.
- [ ] FPS/latency are measured on named devices/browser versions.
- [ ] Evaluation uses participant-level train/test separation if ML is trained.

## Privacy and safety
- [ ] No raw video persisted by default.
- [ ] Camera data flow is clearly described before permission.
- [ ] No face recognition or identity matching.
- [ ] Consent and deletion processes are implemented.
- [ ] User can stop camera immediately.
- [ ] No sparring/weapon/throw/high-impact content in self-guided MVP.
- [ ] AI limitation and instructor-not-replaced statements are visible.
- [ ] User data access is restricted to the user unless explicit sharing consent exists.

## Backend and quality
- [ ] Migrations apply cleanly from an empty database.
- [ ] Auth/role checks pass.
- [ ] User A cannot read User B's practice sessions.
- [ ] Restricted cultural material cannot leak to public API.
- [ ] Unverified partner cannot appear publicly.
- [ ] Content permission revocation affects access correctly.
- [ ] Unit, integration, E2E, lint, typecheck, and build pass.
- [ ] Error handling and loading/empty states are covered.
- [ ] No secrets committed.
- [ ] README/setup instructions are accurate.

## Pilot readiness
- [ ] Instructor comparison protocol approved.
- [ ] Beginner usability test completed.
- [ ] Learning pilot protocol and consent approved.
- [ ] Known limitations documented.
- [ ] Partner accepts the public demo content and attribution.
