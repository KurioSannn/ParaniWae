# UI Design Prompt - SILATARA

Use this prompt in Figma AI, Google Stitch, or as the brief for the designer. It complements `DESIGN.md` and `execution/UI_HANDOFF.md`; it does not replace product/cultural validation.

---

You are a senior product designer designing **SILATARA**, an Indonesian cultural-learning web platform for pencak silat. Design a polished, production-oriented responsive web application with a calm, premium, culturally grounded identity.

## Product context

SILATARA is not a fight game, combat training simulator, or generic martial-arts marketplace. It helps a new generation discover, understand, and safely learn pencak silat while preserving partner-approved movement knowledge and connecting learners to real schools/instructors.

The product has five first-release pillars:
1. Heritage Explorer: stories, tradition/style, regional context, terminology, instructor attribution, source, permission, validation status.
2. Academy: structured beginner lessons with professional instructor references.
3. AI Practice Coach: webcam-based pose/hand landmark practice, quality checks, transparent movement feedback, text/voice correction.
4. Progress: personal practice history and improvement.
5. Community: verified partner schools/instructors and a route to real classes.

The MVP starts with one partner tradition and a small approved set of safe solo beginner movements. Do not design the product as though 100 movements, all Indonesian styles, or a nationwide school directory already exist.

## Core story

A curious beginner discovers a partner tradition -> reads its context -> selects a beginner lesson -> watches an instructor -> checks camera setup -> practices -> receives respectful, actionable correction -> repeats -> sees progress -> finds a verified school for an in-person class.

## Visual art direction

- Contemporary Indonesian cultural institution meets thoughtful learning product.
- Use forest green / evergreen, warm ivory / parchment, muted sage, and restrained bronze accents.
- Working palette: `#17231F`, `#1E3B32`, `#315C4D`, `#78917F`, `#F6F2E9`, `#FCFBF7`, `#B9854F`, `#A95743`, `#52605A`, `#E4E1D8`.
- Use clean sans-serif typography (Plus Jakarta Sans or similar for headings; Inter/system for UI/body).
- Use generous whitespace, clear hierarchy, disciplined card usage, fine warm borders, subtle shadows, and readable content width.
- Use authentic, licensed partner photography where available. Otherwise use neutral placeholders. Never invent a real instructor, school, traditional costume, historical artefact, or cultural symbol.
- If using a batik/ornamental pattern, it must be subtle, sourced, and approved; do not use sacred or culturally specific patterns as decoration without permission.

Avoid:
- generic purple/blue AI gradients;
- neon/cyberpunk HUD;
- fight-game scoreboards, flames, aggressive red/black fight poster aesthetic;
- excessive gold/ornamental decoration;
- glassmorphism everywhere;
- stock photos that misrepresent the selected tradition;
- fake user counts, partner logos, ratings, testimonials, or AI accuracy badges.

## Screens to deliver

### Public web
1. Landing page: hero, problem/mission, product loop, AI coach explainer, heritage preview, community pathway, safety/ethics, footer.
2. Heritage Explorer: search and filters; cards with tradition/style, region, short context, source/partner, verification label.
3. Heritage detail: origin/context, terms, movement/knowledge modules, approved media, contributors, last validated, access label, related course.
4. Academy listing: beginner learning path, course cards, level/status/duration/safety.
5. Course detail: outcomes, instructor profile, module list, prerequisites, cultural context, CTA.
6. Community directory: user-selected city/region filter; verified partner cards only; no fake ratings.
7. Partner detail: style taught, instructors, official contact, location, class schedule if verified, trial-class information.

### Learner app
8. Dashboard: continue learning, next lesson, recent practice, cultural discovery, community CTA.
9. Lesson player: instructor reference video, step-by-step phases, notes, cultural context, safety, start practice.
10. Camera setup: explanation of camera use/data, opt-in permission, lighting/framing checklist, reference orientation, alternative without camera.
11. Live AI practice: large full-body camera stage, subtle skeleton overlay, reference panel, current phase, small correction card, voice toggle, pause/stop, quality state.
12. Assessment result: score only if valid, component breakdown, phase feedback, confidence/quality status, repeat CTA, instructor pathway, disclaimer.
13. Progress: personal history, movement-level progress, repeated improvement areas, learning completion, no public leaderboard.
14. Profile/privacy: consent, data policy, account settings, accessibility/audio settings.

### Partner/admin (design as later-stage or low-fidelity)
15. Partner dashboard/profile.
16. Content submission/review with permission, attribution, and status.
17. Movement reference/rubric review screen.

## Critical live practice states

Design each state distinctly:
- idle / camera not requested;
- permission requested;
- permission denied;
- no camera available;
- model loading;
- no body detected;
- body partially out of frame;
- low lighting/occlusion;
- multiple people in frame;
- camera/reference orientation mismatch;
- ready to practice;
- detecting/analysing;
- not assessable;
- correction available;
- completed;
- error and retry.

Use concise Bahasa Indonesia. Example feedback tone:
- “Posisi tubuh belum terlihat penuh. Mundurkan kamera sedikit.”
- “Bagian ini belum dapat dinilai karena tangan tertutup.”
- “Coba ulangi fase kedua dengan memperhatikan posisi lengan pada referensi.”
- “Latihan tersimpan. Lihat bagian yang bisa kamu perbaiki berikutnya.”

Never use “kamu gagal”, “salah total”, or shame-based language.

## Component and token deliverables

Create a design system with:
- color tokens, type scale, spacing, border, shadow, radii, breakpoints;
- primary/secondary/tertiary buttons, inputs, tabs, chips, cards, badges, accordions, dialogs, tooltips;
- HeritageCard, CourseCard, PartnerCard, InstructorCard;
- SourceAttribution, ValidationBadge, AccessScopeBadge;
- MovementPhaseStepper, VideoReference, CameraFrameGuide, LandmarkOverlay;
- AssessmentBreakdown, CorrectionCallout, VoiceFeedbackControl, ProgressChart;
- SafetyNotice, PrivacyNotice, NotAssessableState, EmptyState, ErrorState, LoadingSkeleton.

All controls need default, hover, focus, disabled, loading, and error states. Components must be keyboard accessible, semantically labelled, and responsive.

## Language and content rules

- Default language: Bahasa Indonesia.
- Product name: SILATARA (working name, trademark not checked).
- Descriptor: AI-Powered Pencak Silat Heritage & Learning Platform.
- Tagline: “Preserving the Heritage. Empowering the Next Generation.”
- Indonesian line: “Warisan Gerak, Generasi Bergerak.”
- Do not imply UNESCO endorsement of SILATARA. You may reference that pencak silat was inscribed by UNESCO in 2019 with a source link.
- Do not make cultural claims or show cultural assets that are not sourced/approved.
- Mark all sample content clearly as demo.

## Handoff requirements

Deliver:
- Figma pages named `00 Foundations`, `01 Public Web`, `02 Learner App`, `03 AI Practice`, `04 Community`, `05 Partner Portal`, `06 Components`, `07 Responsive`.
- High-fidelity desktop and mobile variants for all core screens.
- Clickable prototype for the main learner flow.
- An annotated live-practice interaction spec.
- A reusable component library and token sheet.
- Export-ready SVG/icon/image assets with attribution/permission notes.
- A page-to-component mapping so frontend developers can implement without guessing.

Before final delivery, review whether the UI communicates the cultural mission, privacy, partner authority, AI limitations, and next step to a real school. Design for credibility and usability, not visual novelty alone.
