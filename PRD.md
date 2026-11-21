# Product Requirements Document (PRD) - SILATARA

**Version:** 1.0  
**Status:** Proposed / requirements to validate  
**Primary market:** Indonesia  
**Primary language:** Bahasa Indonesia  
**Platform:** Responsive web application; desktop/laptop webcam experience is the primary AI practice target.

## 1. Product summary

SILATARA is a partner-led digital learning and cultural preservation platform for pencak silat. It combines a curated cultural archive, structured instruction, AI-assisted solo practice, learning analytics, and verified connections to real schools/instructors.

## 2. Goals

### Product goals

1. Improve access to trustworthy beginner pencak silat learning.
2. Preserve partner-approved knowledge, movement references, terminology, and context.
3. Help learners understand and correct selected movements through transparent AI feedback.
4. Encourage progression from independent learning to participation in real cultural communities.
5. Give instructors/partners attribution, content control, and a path to economic benefit.

### Non-goals for MVP

- Replacing a human instructor.
- Certifying rank/belt, competitive eligibility, or combat effectiveness.
- Teaching sparring, fighting tactics, weapon use, throws, or dangerous techniques without supervision.
- Covering every pencak silat style or perguruan in Indonesia.
- Building a social network, user-vs-user competition, public leaderboards, or an open marketplace.
- Automatically deciding cultural authenticity or ownership.
- Storing raw camera video by default.

## 3. Target users and personas

### P1 - Curious beginner (primary)

- Age: MVP account target 17+; younger audiences require a separate guardian/safeguarding design.
- Has interest in Indonesian culture or martial arts but little/no formal silat experience.
- Needs an understandable learning path, a low-pressure starting point, and clear guidance.
- Success: completes a safe beginner lesson, understands one cultural context item, practices a movement, and knows where to continue in person.

### P2 - Active learner / student

- Already attends or has attended a school.
- Wants to review instructor-approved fundamentals and track personal practice.
- Success: can revisit lessons and compare progress without mistaking an app score for formal grading.

### P3 - Instructor / maestro

- Holds knowledge and authority within a particular tradition/school.
- Needs control over what is documented, how it is explained, where it is accessible, and how their contribution is credited/compensated.
- Success: can review a movement reference, approve content, and see how it is represented.

### P4 - Partner-school administrator

- Manages school profile, contact, schedules, trial class details, and approved teaching content.
- Success: receives qualified beginner enquiries and keeps public information accurate.

### P5 - Platform administrator / cultural editor

- Maintains platform quality, user access, partner verification, content status, rights/consent, and moderation.

## 4. Jobs to be done

- When I am curious about pencak silat, I want to understand its cultural meaning and regional diversity before choosing a learning path.
- When I am a beginner, I want to learn basic movements privately and safely before I attend a class.
- When I practice, I want actionable feedback about observable movement differences, not just a vague score.
- When I improve, I want to see progress over time and know what to practice next.
- When I am ready, I want to find a credible school or instructor near a location I choose.
- When I am a cultural practitioner, I want to control attribution, permissions, and access to the knowledge I contribute.

## 5. Information architecture

### Public website

- `/` - landing page
- `/heritage` - cultural archive index
- `/heritage/[slug]` - tradition/style detail
- `/academy` - course catalogue
- `/academy/courses/[slug]` - course detail
- `/community` - verified school/instructor directory
- `/community/[slug]` - partner detail
- `/about`, `/safety`, `/privacy`, `/terms`

### Learner application

- `/app` - learner dashboard
- `/app/learning` - enrolled/in-progress learning paths
- `/app/lessons/[slug]` - lesson player
- `/app/practice/[movementId]` - practice setup and camera check
- `/app/practice/[movementId]/session` - guided practice and assessment
- `/app/practice/results/[sessionId]` - results and correction breakdown
- `/app/progress` - personal learning analytics
- `/app/profile` - settings, privacy, consents

### Partner / admin (MVP-lite or later)

- `/partner` - partner dashboard
- `/partner/profile` - partner profile and public information
- `/partner/content` - approved content management (later if time)
- `/admin` - platform moderation, verification, rights/consent review

## 6. Core user flow

1. Visitor lands on the site and understands that this is cultural learning, not combat training.
2. Visitor explores a verified tradition and reads its context, source, and partner information.
3. Visitor opens a beginner learning path and views an instructor demonstration.
4. Visitor creates/signs into an account and accepts privacy/safety notices.
5. User opens a practice lesson and explicitly grants camera permission.
6. System checks lighting, framing, body visibility, camera orientation, and single-person conditions.
7. User watches the reference and performs only the selected safe solo movement.
8. AI processes landmarks locally, detects quality/visibility, and runs the approved assessment.
9. System shows per-phase/per-component feedback, score only when valid, and a clear recommendation.
10. User repeats the movement, compares practice sessions, and stores progress.
11. User can browse verified partner schools and contact/attend a class.

## 7. Functional requirements

Priority legend: P0 = must for MVP; P1 = should for first public pilot; P2 = later.

### FR-01 Cultural archive

- P0: show a partner-approved tradition/style profile.
- P0: show provenance fields: source partner, instructor/validator, review status, content permission, last validated date.
- P0: show cultural context, history, terminology, and approved media as supplied by partner.
- P0: mark content as public, partner-only, or restricted.
- P1: search/filter by region, style, and topic.
- P1: provide citations/attributions for each article or asset.
- P2: multi-tradition expansion and advanced cross-linking.

### FR-02 Structured academy

- P0: show beginner learning path and progress state.
- P0: provide instructor-led video or approved visual reference.
- P0: lesson contains learning objectives, safety notes, phases, common mistakes, and cultural context.
- P0: user can mark lesson complete.
- P1: short knowledge checks and quizzes.
- P2: adaptive recommendation and premium lessons.

### FR-03 Camera setup

- P0: camera starts only after explicit user action.
- P0: explain why camera is needed and whether video is stored (default: it is not).
- P0: check one-person framing, full-body visibility, lighting, camera angle, and landmark confidence.
- P0: provide a clear fallback when browser/device permissions are unavailable.
- P0: allow user to stop camera instantly.
- P1: device setup guide and performance self-check.

### FR-04 AI movement assessment

- P0: support only the partner-approved movement set.
- P0: use pose + hand landmarks only where the movement rubric needs them.
- P0: associate every assessment with movement ID, style/partner ID, rubric version, and reference version.
- P0: evaluate only instructor-approved observable criteria.
- P0: quality gate prevents scoring when required landmarks are missing, occluded, or low-confidence.
- P0: show score breakdown and text feedback derived from approved correction rules.
- P0: label assessment as practice guidance, not formal grading.
- P1: voice guidance, configurable volume and mute.
- P1: temporal sequence comparison and phase-level review.
- P2: learned temporal models only after adequate permitted data and baseline comparison.

### FR-05 Progress tracking

- P0: store assessment result, movement, date, score breakdown, and rubric version.
- P0: show personal history and best/recent result.
- P0: show what to practice next based on approved learning sequence.
- P1: progress chart and repeated-error trend.
- P2: instructor-visible learner progress with user consent.

### FR-06 Community directory

- P0: show manually verified partner school(s) with region/city, address, description, official contact, and class/trial information if approved.
- P0: mark verified status and last review date.
- P0: no fabricated schools, ratings, schedules, or testimonials.
- P1: filters by user-selected city/region and style.
- P2: booking and payments after partner validation.

### FR-07 Partner content workflow

- P1: partner/instructor can submit movement/content updates for review.
- P1: platform can record rights/consent, source attribution, and approval history.
- P2: partner portal for classes, content revenue, and analytics.

### FR-08 Administration

- P0: platform admin can create, review, approve, unpublish, or restrict content.
- P0: all content with cultural or media rights must have an owner/source and permission status.
- P0: audit trail for partner/content verification changes.
- P1: moderation report and takedown workflow.

## 8. Non-functional requirements

- Performance: responsive interface; AI inference must not freeze the UI. Benchmark on defined target devices before claiming real-time performance.
- Reliability: save completed sessions safely; handle camera denial, model load errors, network loss, and low-confidence frames.
- Security: secure session handling, input validation, role-based access control, rate limits, secret management, and audit logs for privileged changes.
- Privacy: on-device processing by default; no raw video persistence by default; collect only data needed for learning and service operation.
- Accessibility: keyboard operation for non-camera parts, clear contrast, captions/transcripts for instructional media where available, readable text, reduced-motion support, and non-audio alternatives to voice guidance.
- Localization: Bahasa Indonesia first; future local-language content must be approved by the relevant community.
- Cultural correctness: all partner-style standards and sensitive content require documented validation.
- Maintainability: typed contracts, automated tests, versioned movement rubrics, migrations, and reproducible local development.

## 9. Assessment and scoring requirements

- Score must be derived from a versioned instructor-approved rubric, not arbitrary/random values.
- The exact weights are not fixed in this PRD; they must be co-designed with the partner instructor and recorded in `movement_rubric_version`.
- Distinguish `not_assessable` from `incorrect`. Missing/occluded landmarks are not a learner failure.
- Show confidence/quality status where appropriate.
- Do not use a single aggregate score alone; display components and explain what they mean.
- Never imply that camera-based scoring measures force, real combat effectiveness, intent, character, discipline, or formal rank.

## 10. Content and rights requirements

Every cultural asset must include:
- source and creator/performer where known;
- partner/instructor attribution;
- permission/license and allowed uses;
- access level;
- consent date/version;
- restrictions (no download, no public playback, educational only, etc.) where applicable;
- review owner and review date.

Do not scrape or reuse training videos from social media without permission. Do not publish sacred/restricted materials unless the knowledge holder explicitly authorizes it.

## 11. Success metrics

### Product adoption
- activation: user starts first lesson;
- lesson completion rate;
- practice-session completion rate;
- repeat practice within 7 days;
- directory click/contact/trial-class interest.

### Learning
- pre/post movement assessment by blinded instructor;
- expert-AI agreement;
- improvement in partner-defined movement criteria;
- retention after a defined follow-up interval;
- user comprehension of cultural context.

### Technology
- valid landmark frame rate;
- not-assessable rate;
- inference latency/FPS on benchmark devices;
- per-movement Macro F1 / precision / recall if classification is used;
- joint-angle error against an agreed reference where a reliable ground truth exists;
- inter-rater/instructor agreement and confidence intervals.

### Cultural/community impact
- number of partner-approved knowledge items;
- number of validated movements and instructors;
- number of active partner schools;
- number of users who proceed from digital learning to an actual class;
- partner satisfaction and perceived fairness of attribution/benefit-sharing.

Do not set numeric public targets until baseline data and pilot results exist. Targets belong in a research/experiment plan and must be clearly labeled as targets, not outcomes.

## 12. MVP acceptance criteria

A release candidate is acceptable only if:
1. One partner tradition and its beginner movement set are documented with approval evidence.
2. At least one complete learning journey works end-to-end.
3. Camera permission is explicit and can be revoked/stopped.
4. The system can detect and show landmarks on supported devices.
5. The system refuses to score low-quality input and explains why.
6. A movement assessment is derived from a versioned rubric.
7. Feedback is traceable to instructor-approved rules.
8. A user can save and review a session.
9. The directory contains only verified partner information.
10. Product, privacy, safety, and content-rights notices are visible.
11. Automated tests, manual smoke checks, and a live demo scenario pass.

## 13. Risks

- Cultural oversimplification or false standardization across styles.
- AI false correction due to camera angle, body proportions, occlusion, or unvalidated thresholds.
- Unsafe unsupervised practice.
- Lack of long-term partner participation.
- Rights/consent gaps for videos, music, movement knowledge, and oral history.
- Overbuilding too many modules before validating the first learning loop.
- Eligibility mismatch with BUDAYA GO! 2026's 31 March 2026 product-availability cutoff.

## Addendum 2026-11-21: public-first knowledge (owner directive; source of truth: `CLAUDE.md`)
- **Public pages** (`/heritage`, `/library`, `/academy`, `/community`, `/heritage/referensi`) show source-backed
  knowledge without login: traditions and regional terms, exploration across 38 provinces, 43 documented movements
  (23 animated, with pause and speed controls), 2 courses / 16 lessons with quizzes, and the source ledger.
- **Login** only for enrollment, progress, practice history, Practice Studio, Studio/administration, and private pilots.
- **Content basis**: `source_backed` (editorial review), `official_curriculum` (partner confirmation),
  `partner_restricted` (owner access). Acceptance: anonymous users can read every item of public knowledge; no
  `[DEMO]`/development narration on public pages; no broken internal links (link checker).

