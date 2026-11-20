# API Contracts - Initial Draft

These are product-level contracts, not an instruction to implement every endpoint immediately. Confirm the repository's routing and auth conventions first.

## 1. General rules

- JSON over HTTPS.
- Version API routes, for example `/api/v1/...`.
- Use consistent error format and request IDs.
- Authenticate and authorize every private route.
- Validate IDs and ownership server-side.
- Do not accept raw camera video in the default practice endpoint.
- Store rubric/reference versions on every assessment.

### Standard error envelope

```json
{
  "error": {
    "code": "PRACTICE_NOT_ASSESSABLE",
    "message": "Tubuh belum terlihat penuh. Atur ulang posisi kamera lalu coba lagi.",
    "details": {"reason": "LOW_BODY_VISIBILITY"},
    "request_id": "req_example"
  }
}
```

## 2. Public heritage endpoints

- `GET /api/v1/traditions` - list approved public traditions.
- `GET /api/v1/traditions/{slug}` - tradition detail with sources, contributors, access scope.
- `GET /api/v1/movements?tradition_id=...&practice_mode=solo_beginner` - approved movement list.
- `GET /api/v1/movements/{id}` - movement detail, phases, approved public references, safety notes.

Do not return restricted content to an unauthorized user.

## 3. Learning endpoints

- `GET /api/v1/learning-paths`
- `GET /api/v1/learning-paths/{slug}`
- `POST /api/v1/lessons/{lesson_id}/progress`
- `GET /api/v1/me/learning-progress`

## 4. Practice endpoints

### Create session

`POST /api/v1/practice-sessions`

Request:
```json
{
  "movement_id": "uuid",
  "rubric_version_id": "uuid",
  "reference_version_id": "uuid",
  "camera_orientation": "front",
  "client_assessment_version": "0.1.0"
}
```

Response:
```json
{
  "session_id": "uuid",
  "status": "started",
  "movement": {"id": "uuid", "name": "Approved Movement Name"},
  "rubric_version": "v1.0",
  "camera_guidance": {"orientation": "front", "full_body_required": true}
}
```

### Complete session with summary

`POST /api/v1/practice-sessions/{session_id}/complete`

Request:
```json
{
  "status": "completed",
  "duration_ms": 24500,
  "quality_summary": {
    "valid_frame_ratio": 0.91,
    "required_landmark_coverage": 0.96,
    "dropped_frame_ratio": 0.04
  },
  "assessment": {
    "overall_score": 78,
    "score_status": "valid",
    "items": [
      {
        "criterion_key": "example_criterion",
        "phase_id": "uuid",
        "status": "needs_correction",
        "measured_value": 34.2,
        "confidence": 0.88,
        "correction_rule_id": "uuid"
      }
    ]
  }
}
```

Response:
```json
{
  "session_id": "uuid",
  "status": "completed",
  "score_status": "valid",
  "overall_score": 78,
  "result_url": "/app/practice/results/uuid"
}
```

If quality is inadequate, use:
```json
{
  "status": "not_assessable",
  "quality_summary": {"required_landmark_coverage": 0.42},
  "assessment": {"overall_score": null, "items": []},
  "not_assessable_reason": "LOW_BODY_VISIBILITY"
}
```

Do not trust client-supplied scores without server-side schema and authorization validation. For an MVP, the backend may persist client assessment output with an explicit `client_assessment_version`; later server-side reproducibility/validation can be added.

### Read result and history

- `GET /api/v1/practice-sessions/{id}`
- `GET /api/v1/me/practice-sessions?movement_id=...`
- `GET /api/v1/me/progress`

## 5. Community endpoints

- `GET /api/v1/partners?city=...&tradition_id=...`
- `GET /api/v1/partners/{slug}`
- `POST /api/v1/partner-enquiries` (only after privacy/anti-spam design)

Only verified, consented partner listings appear publicly.

## 6. Partner/admin endpoints (P1)

- `POST /api/v1/partner-content-submissions`
- `GET /api/v1/partner/{id}/content-submissions`
- `POST /api/v1/content/{id}/review-decision`
- `POST /api/v1/movements/{id}/rubrics`
- `POST /api/v1/rubrics/{id}/approve`

Every approval/restriction change must create an audit record.

## 7. API contract tests

- unauthenticated private request returns 401;
- cross-user practice result access returns 403/404;
- restricted cultural material is not returned publicly;
- unverified partner does not appear in public directory;
- invalid movement/rubric/version relationship is rejected;
- `not_assessable` has no numeric score;
- missing/expired permission blocks public asset use;
- user can revoke optional consent and data lifecycle follows policy.
