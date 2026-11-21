# SILATARA - UX/UI Design Specification

**Audience:** UI/UX designer, frontend developer, product owner, and Claude Code.  
**Design intent:** credible cultural learning product, not a combat game or generic AI dashboard.

## 1. Design north star

SILATARA should feel like a modern cultural-learning institution: warm, disciplined, trustworthy, human, and rooted in Indonesian heritage. The interface should communicate that the platform is built with real pencak silat practitioners and instructors.

### Experience principles

1. **Culture before spectacle.** Use meaningful cultural context and real partner-approved imagery instead of decorative motifs without explanation.
2. **Calm confidence.** The UI should help a beginner feel safe to start, not judged or intimidated.
3. **Instructor authority remains visible.** Show instructor attribution, partner source, validation status, and version of the reference used.
4. **Explain, do not shame.** Feedback uses constructive language; no red “failure” theatrics, public ranking, or humiliating comparisons.
5. **Show the evidence.** Scores, progress, and AI status must be transparent and appropriately qualified.
6. **One focused action per screen.** The learning/practice journey should not feel like an analytics console.
7. **Responsive, but camera-first desktop.** Public pages and archive work on mobile. Full-body camera practice should clearly recommend a laptop/desktop and provide mobile support only if tested.

## 2. Visual direction

### Proposed palette

The palette is a working direction; test it for contrast and real photography before finalizing.

| Token | Hex | Use |
|---|---|---|
| `ink-950` | `#17231F` | Primary text, dark navigation |
| `forest-900` | `#1E3B32` | Main brand green |
| `forest-700` | `#315C4D` | Primary buttons and active states |
| `sage-500` | `#78917F` | Secondary surfaces and diagrams |
| `parchment-100` | `#F6F2E9` | Main warm background |
| `paper-50` | `#FCFBF7` | Cards and reading surfaces |
| `bronze-500` | `#B9854F` | Restrained accent / cultural detail (dekoratif, ikon, garis; **bukan teks kecil**: kontras 2,9:1) |
| `bronze-700` | `#85592A` | Teks aksen/eyebrow (kontras ≥5,4:1 pada `parchment-100`, ≥5,9:1 pada `paper-50`; diukur) |
| `clay-600` | `#A95743` | Caution and destructive actions (not score shame) |
| `slate-600` | `#52605A` | Secondary text |
| `line-200` | `#E4E1D8` | Dividers and borders |

Avoid large neon green/red combinations, black-and-red fight poster aesthetics, loud gradients, glossy glassmorphism, and excessive gold ornament.

### Typography

- Headings: Plus Jakarta Sans or a similarly legible contemporary sans-serif.
- Body/UI: Inter or system sans-serif.
- Cultural quotations/long reading: readable serif may be used selectively, never for small controls.
- Use consistent type scale. Avoid oversized hero headings on internal app pages.
- Do not embed text in images. All meaningful copy should remain accessible HTML text.

### Shape, imagery, and texture

- Cards: 12-16px radius, thin warm border, very subtle shadow only when needed.
- Buttons: clear hierarchy, 10-12px radius or restrained pill for a single CTA family.
- Use real, licensed images from the partner school/instructor whenever available.
- Every image needs attribution/source metadata in the content model.
- If no licensed image exists, use a designed neutral placeholder, not an unlicensed stock image or fake historical photo.
- Cultural patterns may appear as a very subtle, sourced background detail. Do not use a sacred motif as decoration without partner permission.

### Icons

Use a consistent outline icon set such as Lucide. Do not use emoji as interface icons. Icons must have text labels when action meaning is not obvious.

## 3. Layout system

- Desktop max content width: 1200-1280px.
- Reading content max width: 720-800px.
- Main app navigation: 240-260px sidebar on wide screens; collapsible to compact rail/mobile drawer.
- Grid: 12 columns desktop, 8 tablet, 4 mobile.
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64, 80px.
- Main content padding: 24-32px desktop; 16-20px mobile.
- Breakpoints (working): 640px, 768px, 1024px, 1280px.

## 4. Navigation model

### Public top navigation

- SILATARA brand
- Jelajahi Warisan
- Akademi
- Perguruan
- Tentang
- Masuk / Mulai Belajar

### Learner app navigation

- Ringkasan
- Jalur Belajar
- Latihan AI
- Progres
- Jelajahi Perguruan
- Profil & Privasi

### Partner navigation (later)

- Ringkasan Mitra
- Profil Perguruan
- Materi & Gerakan
- Persetujuan & Atribusi
- Kelas & Jadwal
- Analitik

## 5. Page-by-page requirements

### 5.1 Landing page `/`

**Purpose:** quickly explain the product's cultural mission, learning loop, and credibility.

Sections:
1. Hero: “Pelajari Gerak. Pahami Warisan.” or approved final headline; short explanation; CTA `Mulai Belajar` and secondary `Jelajahi Warisan`.
2. Trust strip: “Dikembangkan bersama instruktur/mitra budaya” only after partnership is confirmed. Before confirmation use neutral copy such as “Dirancang dengan pendekatan validasi instruktur”.
3. Product loop: Discover -> Learn -> Practice -> Connect.
4. AI coach explanation with a real product UI screenshot, not fake demo claims.
5. Heritage archive preview: one partner tradition only; show source/validation label.
6. Community pathway: find a verified school.
7. Safety and cultural respect principles.
8. Footer: sources, privacy, contact, accessibility.

Do not claim UNESCO endorsement of SILATARA. It is acceptable to say pencak silat was inscribed by UNESCO in 2019, with a source link, but do not imply UNESCO approves this product.

### 5.2 Heritage explorer `/heritage`

- Search and filter by tradition/style, region, topic.
- Cards should surface name, region, short context, partner/source, and validation status.
- Use `Terverifikasi oleh mitra` only when the actual content item has been approved.
- Empty state explains that the initial catalogue is intentionally focused and will expand through partner collaboration.

### 5.3 Heritage detail `/heritage/[slug]`

Content structure:
- Hero with tradition name, region, partner, and source.
- “Mengenal tradisi ini” summary.
- Historical/cultural context with citations/attribution.
- Movement or knowledge sections.
- Terms glossary.
- Approved video/audio gallery.
- “Belajar bersama” CTA to relevant course.
- Permission/access label if applicable.
- Contributors and last validated date.

Avoid a generic encyclopaedia page. Explain why the knowledge matters and who maintains it.

### 5.4 Academy `/academy`

- Learning paths by level and partner tradition.
- Clear level, prerequisites, estimated lesson time, equipment/safety notes.
- Show which material is available and what is planned. Never show planned lessons as active.

### 5.5 Course detail `/academy/courses/[slug]`

- Learning outcomes.
- Instructor profile and attribution.
- Course modules and lessons.
- Cultural context.
- Safety requirements.
- Start/continue CTA.
- Partner/source and validation metadata.

### 5.6 Lesson player `/app/lessons/[slug]`

- Video or approved reference on left/main column.
- Lesson step list and instructions on right.
- Subsections: tujuan, demonstrasi, fase gerak, kesalahan umum, konteks budaya, keselamatan.
- CTA `Mulai latihan dengan AI` only for movements with an approved assessment rubric.
- If a movement is not AI-assessable, show normal practice guidance; do not show a disabled AI feature as if it exists.

### 5.7 Practice setup `/app/practice/[movementId]`

Before camera:
- Movement title, style/partner reference, instructor, camera orientation, safe practice area.
- Pre-flight checklist: full body in frame, adequate light, no other person in frame, stable device, enough space, shoes/surface instructions per partner.
- Explain camera data handling before permission request.
- Camera starts only after click.
- Allow “Lihat video tanpa kamera” fallback.

### 5.8 Live practice `/app/practice/[movementId]/session`

Desktop layout:
- Main camera stage with skeleton overlay.
- Reference video/picture-in-picture panel.
- Current phase and short instruction.
- Status indicator: `Mendeteksi tubuh`, `Posisi belum terlihat penuh`, `Siap dinilai`, etc.
- Optional current feedback panel. Keep it brief, do not cover the body.
- Pause/stop controls always visible.
- Audio guidance toggle and volume.
- Camera-off control.

Never use aggressive countdowns, fight scoring, opponent imagery, or arcade effects. A neutral preparation cue is fine.

### 5.9 Result page `/app/practice/results/[sessionId]`

- Overall practice summary only when valid.
- Component breakdown, phase-by-phase result, and expert-approved correction.
- Show confidence/coverage and any not-assessable component.
- Compare with previous session when the rubric version is the same; if it changed, explain that scores may not be directly comparable.
- CTA to repeat, return to lesson, or find an instructor.
- Disclaimer: practice aid, not formal grading or rank certification.

### 5.10 Progress `/app/progress`

- Personal-only progress; no public leaderboard in MVP.
- Recent practice, improvement by movement, repeat-error trends, completed lessons.
- Provide context for score changes; do not imply an exact score equals mastery.

### 5.11 Community `/community`

- Search by city/region selected by the user (GPS is optional and opt-in, not required).
- Only verified partners.
- Cards show official name, style/tradition, city, address if public, official contact, schedule if verified, trial options, last checked date.
- No fake ratings, reviews, locations, or distance claims.

### 5.12 Partner detail `/community/[slug]`

- Partner identity and verification marker.
- Traditions/styles taught.
- Instructor(s) and credentials as supplied and verified.
- Official contact, class schedules, trial-class details, accessibility notes.
- How to join.
- Link to related learning path.

### 5.13 Profile & privacy

- Name and basic profile.
- Camera permission explanation.
- Consent state and policy links.
- Data export/delete request or clear account deletion process.
- Audio/visual preferences.

## 6. Component inventory

- `PublicHeader`, `AppSidebar`, `MobileNavDrawer`.
- `HeritageCard`, `PartnerCard`, `InstructorCard`, `CourseCard`, `LessonRow`.
- `ValidationBadge`, `SourceAttribution`, `AccessScopeBadge`, `LastReviewedText`.
- `MovementPhaseStepper`, `ReferenceVideoPlayer`, `CameraPermissionPanel`.
- `CameraFrameGuide`, `PoseOverlayCanvas`, `LandmarkQualityIndicator`.
- `AssessmentScoreCard`, `MovementMetricRow`, `CorrectionCallout`, `VoiceFeedbackControl`.
- `ProgressChart`, `PracticeHistoryTable`.
- `SafetyNotice`, `PrivacyNotice`, `NotAssessableState`, `ErrorBoundary`, `LoadingSkeleton`, `EmptyState`.

Components should be reusable, typed, and accessible. Avoid building one monolithic page component.

## 7. Interaction and UI states

Every camera and AI screen must define:
- idle / camera not requested;
- permission request;
- permission denied;
- camera unavailable;
- model loading;
- no body detected;
- full body out of frame;
- low visibility/occlusion;
- one-person check failed;
- ready to practice;
- detecting / analyzing;
- not assessable;
- assessment complete;
- error / retry.

Every archive/community page must define loading, empty, error, unverified, restricted, and unavailable states.

## 8. Copy and tone

- Indonesian first, warm and respectful, not overly formal.
- Use “latihan”, “pembelajaran”, “instruktur”, “maestro”, “perguruan”, “tradisi”, “gerakan”, and “konteks budaya”.
- Avoid “jago berantem”, “mengalahkan lawan”, “petarung hebat”, “AI menentukan sabuk”, or terms that glorify violence.
- Avoid shaming copy such as “Gerakan salah total”. Use “Belum sesuai dengan referensi pada bagian...” or “Coba ulangi dengan memperhatikan...”.
- Use “belum dapat dinilai” rather than “nilai 0” when landmarks are missing.
- Do not show invented testimonials, user counts, school counts, AI accuracy, or partner logos.

## 9. Responsive behavior

- Public content should be fully responsive.
- On mobile, archive and lesson reading should work well.
- Practice screen should show a clear notice when the device cannot provide a reliable full-body view. Do not pretend a close-up phone camera is suitable for full-body assessment.
- On small screens, place camera and feedback in a vertical flow; never overlay critical body areas with large panels.

## 10. Accessibility

- WCAG 2.2 AA target for core UI.
- Visible focus, semantic headings, labels, keyboard navigation, high contrast, reduced motion.
- Voice feedback must have a text equivalent.
- Videos should have captions/transcripts when available and authorized.
- Never rely on color alone to communicate score/status.
- Support zoom and larger text without breaking the practice controls.

## 11. UI quality bar

Reject a screen if it looks like a generic generated dashboard, has arbitrary gradients, decorative charts with no meaning, fake data presented as real, or unlicensed martial arts imagery. Every element must support cultural understanding, learning, practice, trust, or community connection.


## 12. Identitas maskot (sprint 7)
- **Simbol brand tunggal** = maskot pesilat poligon (`Faceted Pencak Silat Warrior.png` di root; salinan kerja `frontend/brand-source/`). Turunan dibuat otomatis oleh `frontend/scripts/build-brand-assets.mjs` (latar hitam → alpha, potongan persegi kepala+lengan untuk ikon). Karakter tidak digambar ulang. Komponen `Brand.tsx` adalah satu-satunya sumber simbol di navbar, footer, sidebar, auth, dan loading.
- **Hero gelap (obsidian)** dengan maskot besar sebagai fokus, tanpa lingkaran/badge — keputusan eksplisit pemilik produk. Ini **mengesampingkan** larangan "black-and-red poster" di §2 hanya untuk hero/CTA/Practice Studio: kontras diredam (obsidian hijau-tua, bukan hitam murni), tipografi serif tenang, aksen emas; seluruh area aplikasi tetap hangat-terang.
- Token tambahan: `obsidian-950 #0f1512`, `obsidian-900 #151d19`, `ember-500 #e8793a`, `ember-700 #a8341e`, `gold-400 #f0b64a`. Warna maskot tidak diubah.

## Public copy policy (2026-11-21)
- Write like a cultural/educational editorial publication, in Bahasa Indonesia, for people: warm, clear, not marketing SaaS, not AI jargon.
- Never show visitors development status, seed/test data, placeholders, approval workflow states, or "belum tersedia" as the main message.
  When information is missing, say it naturally ("Tidak dirinci dalam sumber; tanyakan kepada pelatih").
- References appear as a compact editorial "Rujukan" section (author, year, title, page), not as admin badges.
- Animations show on the page with Jeda/Putar and 0,5×/1×/1,5× controls, and respect `prefers-reduced-motion` (start paused).



## Pembaruan visual 2026-11-21 (desain dari UI designer)
Identitas visual mengikuti landing page dari desainer: **logo resmi** (`public/brand/silatara-logo-full.png`), palet maroon (`forest-*` = #2e0909–#8f2317), cokelat (`chocolate-*`), dan oranye (`emerald-*` = #ea580c…); font **Plus Jakarta Sans** (isi & judul) dan **Cinzel** (aksen merek), di-host sendiri lewat `next/font`; tombol primer bergradien maroon→oranye; kartu `rounded-3xl`; ilustrasi pendekar, awan, dan motif kawung/tumpal (`public/landing`, `AtmosphericClouds`, `SilatMotifs`). Teks aksen kecil memakai `bronze-700` (#9a3412, kontras ≥7:1). Konten landing ditulis ulang dari fitur nyata: **tanpa** testimoni, tier mitra, sertifikat, atau klaim akreditasi. Halaman publik **tidak menampilkan rujukan/halaman kutipan** maupun urusan mitra (API publik membersihkannya lewat `scrub`).
