# Metrics & Analytics Framework

## 1. Measurement principle

Measure product utility, learning, technology reliability, cultural stewardship, and partner benefit. Do not optimize only for time in app, streaks, or scores.

## 2. North-star metric candidate

**Validated learning-to-community progression:** number of learners who complete an approved learning path and then take a verified next step with a partner school (e.g. class enquiry or trial attendance) within a defined period.

This is a candidate metric, not yet validated as the definitive north star.

## 3. Product funnel

1. landing visit;
2. heritage item opened;
3. learning path started;
4. lesson completed;
5. first practice started;
6. assessable practice completed;
7. repeat practice;
8. partner directory opened;
9. partner contact/class enquiry;
10. verified class attendance (only if partner/user consents to report).

## 4. Event taxonomy

Use neutral event names and avoid sending camera frames or biometric details to analytics.

- `heritage_item_viewed`
- `learning_path_started`
- `lesson_started`
- `lesson_completed`
- `camera_permission_requested`
- `camera_permission_granted`
- `camera_permission_denied`
- `practice_session_started`
- `practice_session_not_assessable`
- `practice_session_completed`
- `correction_shown`
- `practice_repeated`
- `progress_viewed`
- `partner_profile_viewed`
- `partner_contact_clicked`
- `trial_class_interest_submitted`

Do not include raw landmark arrays or exact movement measurements in general product analytics. Keep assessment records in the protected practice data domain.

## 5. KPI definitions

### Product
- activation rate = users who start a lesson / new registered users;
- first practice conversion = users with completed practice / users who start a lesson;
- repeat practice rate = users returning for another practice within 7 days / users with first practice;
- learning path completion = completed paths / started paths;
- partner contact rate = partner contact actions / users who view partner profiles.

### Technology
- assessable session rate = assessable sessions / all practice sessions;
- landmark coverage = valid required landmarks / required landmarks;
- inference latency p50/p95;
- FPS median on benchmark device;
- camera/model failure rate;
- not-assessable reason distribution.

### Learning
- instructor rubric score delta pre/post;
- error reduction by criterion;
- time to partner-defined beginner threshold;
- short-term retention;
- cultural knowledge pre/post change.

### Culture/partner
- approved content items;
- validated movement items;
- active partner schools/instructors;
- instructor review turnaround;
- percentage of assets with complete source/permission/attribution metadata;
- partner satisfaction;
- partner revenue/leads where applicable and consented.

## 6. Analytics governance

- Use data minimization and documented purpose.
- No default raw video analytics.
- Keep personally identifiable information separate from event telemetry.
- Provide opt-out where required/appropriate.
- Define retention and deletion.
- Report aggregate learning metrics with small-cell suppression where re-identification risk exists.
