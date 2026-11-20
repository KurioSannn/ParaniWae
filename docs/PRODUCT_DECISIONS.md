# Product and Architecture Decisions (ADR-lite)

These decisions are the current working baseline. Change them only with a short rationale and a recorded impact on product, culture, safety, privacy, and delivery.

## PD-001 - Partner-led cultural foundation

**Decision:** choose the first tradition/style through partner readiness and co-validation, not by selecting a style solely from desk research.  
**Reason:** cultural authority, safety, and authentic teaching require a real knowledge holder.  
**Consequence:** no public AI assessment until the anchor partner and rubric are approved.

## PD-002 - One partner tradition in MVP

**Decision:** MVP begins with one style/partner and about 8-12 candidate fundamental movements.  
**Reason:** a small validated set is stronger than a broad unverified catalogue.  
**Consequence:** architecture must support multiple styles, but initial content is intentionally narrow.

## PD-003 - Digital education subtheme

**Decision:** proposed BUDAYA GO! fit is Inovasi Digital subtheme 4, Pembelajaran dan Edukasi Digital Berbasis Budaya.  
**Reason:** the product's primary function is digital learning and preservation.  
**Consequence:** community directory is a supporting feature, not a second selected subtheme.

## PD-004 - Browser-first practice

**Decision:** prioritize laptop/desktop browser camera practice; responsive public content works on mobile.  
**Reason:** full-body framing is more reliable on a stable, appropriately positioned camera.  
**Consequence:** mobile practice is supported only after it passes the same camera quality tests.

## PD-005 - On-device inference by default

**Decision:** raw camera frames stay in the browser; only assessment summaries are persisted by default.  
**Reason:** minimize personal data and network latency.  
**Consequence:** server-side video analysis is out of MVP unless a separately justified/consented design is approved.

## PD-006 - Deterministic, expert-approved assessment first

**Decision:** begin with geometric/temporal features and explicit rules; do not start with an opaque LLM judge or large neural model.  
**Reason:** small data, explainability, and instructor trust.  
**Consequence:** every criterion and feedback message requires partner approval and versioning.

## PD-007 - `not_assessable` is a first-class result

**Decision:** insufficient visibility/confidence produces `not_assessable`, not zero or an incorrect score.  
**Reason:** capture failure must not be interpreted as learner failure.  
**Consequence:** camera setup and quality feedback are core UX, not technical extras.

## PD-008 - No raw video persistence by default

**Decision:** don't upload/store raw user video by default.  
**Reason:** privacy and data minimization.  
**Consequence:** progress is based on summary/feature outputs; optional research recording needs separate consent and retention controls.

## PD-009 - Human instructor retains authority

**Decision:** AI does not certify rank, mastery, cultural authenticity, artistic quality, or combat effectiveness.  
**Reason:** these exceed what a webcam-based movement metric can establish.  
**Consequence:** UI/marketing must show AI as a practice aid, and instructors remain the authority for progression/assessment.

## PD-010 - Community pathway is a product outcome

**Decision:** connect learners to verified schools/instructors rather than optimizing for endless in-app practice.  
**Reason:** cultural transmission should lead to participation in living communities.  
**Consequence:** measure real partner enquiries/attendance (with consent) as a meaningful outcome.

## PD-011 - Working brand name only

**Decision:** use SILATARA as a working product name.  
**Reason:** selected in product exploration.  
**Consequence:** do not claim trademark/domain availability until checked through official registries and domain providers.

## PD-012 - Competition eligibility is not an engineering workaround

**Decision:** treat 31 March 2026 product availability as a hard competition gate.  
**Reason:** official Juknis.  
**Consequence:** no backdating, fabricated release evidence, or misrepresentation of post-cutoff features.
