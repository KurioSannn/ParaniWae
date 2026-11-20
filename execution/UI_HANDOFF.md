# UI/UX Handoff - Brief for the Designer

## What you are designing

You are designing **SILATARA**, a web-based cultural-learning platform for pencak silat. The product is not a fight game or combat tutorial. It is a respectful digital entry point into Indonesian pencak silat heritage, partner-approved beginner learning, AI-assisted solo practice, and verified connections to real perguruan/instructors.

## Why the product exists

The founder's problem hypothesis is that some young people are interested in pencak silat but hesitate to start because they lack access/information, feel uncomfortable making mistakes in public, or associate the practice with negative incidents involving some individuals/groups. The platform aims to make the first learning step accessible and positive, while leading users toward real instructors. Do not generalize negative conduct to all perguruan/practitioners.

Pencak silat is UNESCO-inscribed intangible cultural heritage (2019) with artistic, sporting, mental-spiritual, self-defence, and regionally diverse dimensions. It is important that the UI does not present one school's style as the single national standard.

## Product pillars

1. **Heritage Explorer:** history, tradition/style, local terms, philosophy, contributors, sources, and access permissions.
2. **Academy:** structured beginner lessons and instructor demonstrations.
3. **AI Practice Coach:** browser camera, pose/hand landmarks, transparent assessment, correction and optional voice feedback.
4. **Progress:** personal learning history and next practice suggestion.
5. **Community:** verified school/instructor directory and route to a real class.
6. **Partner Portal:** later-stage area for content approvals and school operations.

## Main user story

A curious beginner discovers a partner tradition, learns a safe fundamental movement, watches an instructor demonstration, sets up a full-body camera view, practices, receives a clear correction, repeats the movement, sees progress, and finds a real perguruan for continued practice.

## Core pages to design

1. Landing page.
2. Heritage list and detail.
3. Academy list, course detail, lesson player.
4. Camera setup screen.
5. Live practice coach screen.
6. Assessment result screen.
7. Personal progress dashboard.
8. Verified school directory and partner detail.
9. Profile/privacy settings.
10. Later: partner content portal.

## Visual direction

Use a calm, modern, premium, cultural-learning style. Suggested palette: forest/evergreen, warm ivory/parchment, muted sage, and a restrained bronze accent. Avoid generic purple/blue AI gradients, cyberpunk HUDs, fighting-game scoring, excessive glassmorphism, loud red failure states, decorative batik without provenance, and unlicensed stock photos.

Prefer authentic partner-approved photography and instructor demonstrations. If there is no permissioned asset, use a clear placeholder rather than inventing a cultural image/performer.

## Design the AI practice state deeply

The camera screen is the core product experience. It must show:
- camera consent and camera framing guide;
- the full-body stage with a subtle skeleton overlay;
- the instructor reference video;
- current movement phase and simple cue;
- detection status;
- feedback panel that does not cover the user’s body;
- voice toggle, mute, pause, and stop controls;
- a clear “not yet assessable” state for poor lighting/occlusion/framing.

Never make a learner feel publicly judged. Keep results private by default and use constructive language such as “Bagian ini belum sesuai dengan referensi; coba perhatikan posisi...” not “Salah total”.

## Content honesty

Do not invent partner logos, names, bios, school addresses, testimonials, class schedules, AI accuracy, number of users, or cultural-history facts. Use labelled demo content while partner evidence is absent. Every real content item should have source and validation metadata.

## Deliverables from design teammate

- Figma pages: Foundations, Components, Public Web, Learner App, AI Practice, Community, responsive variants.
- High-fidelity desktop and mobile frames for all core routes.
- Clickable prototype of the main learner flow.
- Component states: default, hover, focus, disabled, loading, empty, error, restricted, unverified, not-assessable.
- Design tokens (color, type, spacing, radii, shadow, breakpoints).
- Iconography and image-attribution notes.
- Interaction notes for webcam permission, inference status, correction, and stopping a session.
- Handoff annotations and asset exports.

## Required review questions

- Does a beginner immediately understand that this is a cultural-learning product, not a fighting app?
- Does the page make the role of instructors and cultural partners visible?
- Can users distinguish real approved content from demo/placeholder content?
- Is it obvious why and when camera permission is requested?
- Can users stop the camera at any time?
- Does AI feedback explain the movement in a respectful, actionable way?
- Can users read and operate the app on small screens and with keyboard/screen reader?
