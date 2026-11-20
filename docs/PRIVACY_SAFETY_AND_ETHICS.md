# Privacy, Safety, and Cultural Ethics

## 1. Privacy principles

- Camera is opt-in and only begins after a clear user action.
- On-device inference is the default.
- Raw video is not stored or uploaded by default.
- Do not perform face recognition or identity matching.
- Do not store face landmarks unless there is a documented, partner-approved, user-consented need; MVP should not use face landmarks.
- Persist only necessary session/assessment summaries.
- Explain exactly what is processed, where, and for how long.
- Provide account/data deletion and consent revocation processes.
- Avoid precise GPS. Let users choose a city/region; location permission is optional and separate.

## 2. Consent layers

Separate consent for:
1. account/service terms;
2. camera processing for a practice session;
3. saving practice history;
4. optional sharing of progress with an instructor;
5. optional recording/upload of the user's video for a research pilot;
6. cultural content/performer release (for instructors/partners).

Do not bundle optional video research consent into general account terms.

## 3. Safety rules

- MVP practice content is limited to partner-approved, safe solo beginner movements.
- Exclude sparring, opponent interaction, throws, weapons, acrobatics, high-impact drills, and dangerous techniques from unsupervised home use.
- Show a safe practice-area checklist and warm-up guidance approved by instructor.
- Provide visible stop/pause controls.
- Use “stop if pain/discomfort” guidance.
- Explain that the AI is not an instructor and does not certify rank, competition readiness, or combat ability.
- AI must not provide combat tactics, advice to harm others, or optimization for aggression.

## 4. Fairness and technical limitation

- Camera angle, lighting, clothing, body proportions, mobility differences, and occlusion can change landmark quality.
- Do not punish users for camera failure or inaccessible movement patterns.
- Provide “not assessable” and non-camera learning mode.
- Never infer ability/character from a score.
- Make criteria visible and test across varied bodies/devices; avoid body-size or gender assumptions.
- Allow partner-approved variations and accessibility accommodations where valid.

## 5. Cultural rights and stewardship

- Obtain informed permission and attribution for all partner-originated materials.
- Respect public/community/restricted access levels.
- A partner can only authorize materials within their authority.
- Document license, permission scope, commercial use, derivative use, term, and revocation.
- Do not scrape YouTube/social media and re-host content without permission.
- Respect sacred/restricted knowledge and community rules.
- Agree how any revenue is shared with the instructor/school/knowledge holder.

## 6. Threat model essentials

- Protect authentication credentials and session tokens.
- Use role-based access control and server-side object ownership checks.
- Prevent insecure direct object references to private results/content.
- Validate uploads, file types, size, and storage permissions.
- Avoid exposing private video/object-storage URLs.
- Add rate limits for auth, enquiries, and public APIs.
- Keep audit logs for privileged content/permission changes.
- Use security headers, CSRF protection where applicable, secure cookies, and secret management.

## 7. Compliance work to review with qualified counsel

Before production, review obligations under Indonesian personal data protection law (including UU No. 27 Tahun 2022), consumer/e-commerce rules if payments are introduced, child data safeguards if under-18 users are admitted, intellectual-property rules, and relevant Traditional Knowledge/Communal Intellectual Property governance. This document is an engineering checklist, not legal advice.
