# User Research & Validation Plan

**Status:** plan ready; raw primary research files must be added and audited.

## 1. Evidence currently known

Founder has stated that a questionnaire, peer conversations/interviews, and potential partner communications exist. The source files were not among the files available for this ZIP. Therefore all specific sample sizes, percentages, quotes, and partner commitments remain unknown here.

Create `reference-materials/user-evidence/` and place:
- questionnaire form/export (CSV/XLSX/PDF);
- survey question wording and recruitment method;
- interview notes/transcripts with consent status;
- partner meeting notes/emails/letters;
- observation notes from practice sessions;
- any previous test results.

Do not include unnecessary personal identifiers. Pseudonymize respondent data and store consent evidence separately with access restrictions.

## 2. Research objectives

1. Validate beginner barriers and motivations.
2. Understand whether stigma/perception actually affects willingness to start.
3. Identify the job to be done for an AI-assisted learning product.
4. Learn what instructors consider safe and useful for home practice.
5. Test willingness of schools/instructors to collaborate and benefit.
6. Measure whether the platform changes learning outcomes and actual community participation.

## 3. Survey analysis plan

### Minimum fields to inspect

- respondent eligibility/age band;
- location/region;
- prior pencak silat experience;
- awareness and perception;
- interest in learning;
- barriers to starting;
- preferred learning mode;
- device/camera access;
- willingness to practice at home;
- willingness to join an in-person school;
- features considered useful;
- privacy/camera concerns.

### Analysis principles

- Report sample size and recruitment method.
- Show distributions and denominators for each question.
- Distinguish respondents who already practice from those who do not.
- Avoid treating friends/classmates as a nationally representative sample.
- Separate correlations from causal conclusions.
- Preserve neutral/negative responses; do not only quote supporters.
- If multi-select, state that percentages may exceed 100%.

### Required outputs

- one-page respondent profile;
- descriptive results table;
- key barriers ranked by frequency (not subjective importance unless asked);
- cross-tabs by prior silat experience and age group where sample size permits;
- limitations and sampling bias;
- product decisions linked to each finding.

## 4. Interview plan

Interview at least these roles where accessible:
- beginner/non-practitioner;
- current student;
- instructor/coach;
- senior practitioner/maestro;
- school/organization administrator.

### Sample questions for beginners

- What first made you interested in pencak silat?
- What would make you hesitate before visiting a perguruan?
- What do you believe happens during a first practice session?
- How do you distinguish cultural learning from competitive/combat training?
- Would a private beginner lesson help? Why or why not?
- Which movements do you feel comfortable practicing alone, and which require supervision?
- What would make you trust an AI movement correction?

### Sample questions for instructors

- Which beginner movements are safe for independent practice?
- Which errors are visible from a single RGB camera?
- Which errors require tactile/physical correction or instructor observation?
- What variations are accepted within your style?
- What cultural context must accompany each movement?
- Which material can be recorded and publicly shown?
- What would make a digital platform beneficial or harmful to the school?
- What rights, attribution, review, and revenue arrangements are appropriate?

## 5. Prototype tests

### Usability test

Tasks:
1. Find the partner tradition and understand its context.
2. Start the beginner learning path.
3. Watch a movement lesson.
4. Complete camera setup.
5. Practice one approved movement.
6. Interpret the feedback.
7. Review progress.
8. Find a partner school.

Measure task success, time-on-task, confusion points, perceived trust, and accessibility issues.

### AI feedback comprehension test

Ask learners to interpret the feedback and demonstrate the next correction. If they cannot explain or act on it, the feedback is not useful even if the CV metric is strong.

## 6. Learning-effectiveness pilot

Suggested early feasibility design:
- Group A: approved instructor video + written cue.
- Group B: same video + AI Practice Coach feedback.
- Same movement set, time-on-task, and training conditions.
- Pre/post movement assessment by instructors blinded to group assignment.
- Optional retention check after a pre-defined interval.

Start with a small feasibility pilot (for example, 15-20 learners per group if recruitment allows). This is not automatically a statistically powered efficacy study. Determine sample size through a power analysis before making inferential claims.

Primary outcomes:
- movement quality against instructor rubric;
- change in per-component errors;
- time required to reach an agreed performance threshold.

Secondary outcomes:
- cultural knowledge quiz;
- confidence and social comfort;
- intention to attend a school;
- actual class enquiry/attendance.

## 7. Technical dataset evaluation plan

- Record with written permission.
- Separate data by participant identity into train/validation/test; avoid frame leakage.
- Capture only approved beginner movements.
- Include camera distance/angle, lighting, clothing, body visibility, and device labels.
- Keep at least one held-out group of users not represented in training.
- Keep instructor scoring independent where possible.
- Record inter-rater agreement among instructors before training or scoring the AI.

## 8. Partner validation deliverables

- partner profile and status (prospect / in discussion / pilot / signed);
- meeting note and decision log;
- written permission/consent for each recorded item;
- approved movement/rubric list;
- instructor feedback log;
- sign-off for demo/pilot;
- benefit-sharing agreement or an explicit statement that monetization is not yet agreed.

## 9. Reporting format

Every result should state:
- source file and date;
- sample size and denominator;
- method;
- observed result;
- limitation;
- product decision resulting from the result;
- evidence label (`USER-REPORTED`, `RESEARCH-FINDING`, `TARGET`, etc.).

## 10. Do not do

- Do not invent survey statistics or quotes.
- Do not label the public perception of all pencak silat as negative.
- Do not claim that AI causes an increase in participation before a controlled/credible evaluation.
- Do not publish individual interview notes or identifiable data without consent.
