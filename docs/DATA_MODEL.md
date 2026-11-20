# Data Model - Initial Domain Model

This is an initial conceptual schema. Adapt after repository and auth-provider audit. Use UUID/ULID primary keys, timestamps, soft-delete or archival where appropriate, and foreign-key integrity.

## 1. Core entities

### `users`
- `id`
- `email` (unique, if email auth is used)
- `display_name`
- `role` or role relation
- `status`
- `created_at`, `updated_at`

### `learner_profiles`
- `user_id`
- `experience_level`
- `preferred_language`
- `region_label` (user-entered/selected; avoid precise GPS by default)
- `accessibility_preferences`

### `cultural_traditions`
- `id`, `slug`, `name`
- `region`, `local_name`, `description`
- `cultural_context`
- `public_summary`
- `source_citation`
- `status` (`draft`, `in_review`, `approved`, `restricted`, `retired`)
- `access_scope` (`public`, `community`, `restricted`)
- `created_at`, `updated_at`

### `partners`
- `id`, `name`, `partner_type` (`school`, `community`, `institution`, `individual_master`)
- `official_description`, `region`, `city`
- `public_address`, `official_contact`, `website/social_url`
- `verification_status`, `verified_at`, `last_reviewed_at`
- `public_listing_consent`

### `instructors`
- `id`, `partner_id`, `name_or_public_alias`, `bio`
- `preferred_attribution`
- `credentials_summary` (only verified statements)
- `public_profile_consent`

### `tradition_partners`
- `tradition_id`, `partner_id`
- `relationship_type` (`custodian`, `teaching_partner`, `research_partner`, etc.)
- `authorization_scope`, `approval_status`

### `movements`
- `id`, `tradition_id`, `partner_id`
- `slug`, `name_local`, `name_id`
- `description`, `teaching_objective`, `difficulty_level`
- `practice_mode` (`solo_beginner`, `supervised_only`, `not_for_practice`)
- `safety_notes`, `cultural_context`
- `assessment_enabled`, `status`

### `movement_phases`
- `id`, `movement_id`, `order_index`
- `name`, `instruction`, `reference_start_ms`, `reference_end_ms`
- `observable_criteria_summary`

### `reference_assets`
- `id`, `movement_id`, `partner_id`, `instructor_id`
- `asset_type` (`video`, `image`, `audio`, `document`)
- `storage_key` or external approved URL
- `source_owner`, `attribution_text`, `license_or_permission_ref`
- `access_scope`, `consent_status`, `consent_version`
- `captured_at`, `approved_at`, `version`, `checksum`

### `movement_rubrics`
- `id`, `movement_id`, `version`
- `status` (`draft`, `in_review`, `approved`, `retired`)
- `approved_by`, `approved_at`, `approval_evidence_ref`
- `camera_orientation`, `minimum_visibility_requirements`
- `created_at`

### `rubric_criteria`
- `id`, `rubric_id`, `phase_id`
- `criterion_key`, `name`, `description`
- `measurement_method`, `threshold_or_tolerance_config`
- `weight` (nullable until approved)
- `is_assessable_by_webcam`
- `allowed_variations`, `severity_levels`
- `correction_message_id`

### `correction_messages`
- `id`, `partner_id`, `movement_id`, `criterion_key`
- `message_text_id`, `message_text`
- `voice_text` (optional)
- `approved_by`, `approved_at`, `version`

### `learning_paths`, `courses`, `lessons`
- `learning_paths`: title, description, tradition_id, level, status
- `courses`: path_id, title, instructor_id, partner_id, order/status
- `lessons`: course_id, title, order, content blocks, movement_id (nullable), safety notes

### `lesson_progress`
- `id`, `user_id`, `lesson_id`
- `status`, `started_at`, `completed_at`, `last_position`

### `practice_sessions`
- `id`, `user_id`, `movement_id`, `rubric_id`, `reference_asset_id`
- `status` (`started`, `completed`, `not_assessable`, `error`, `cancelled`)
- `started_at`, `completed_at`, `duration_ms`
- `device_category`, `browser_family` (coarse/limited telemetry)
- `camera_orientation`, `quality_summary`
- `overall_score` (nullable if invalid/not assessable)
- `result_summary`

### `practice_assessment_items`
- `id`, `session_id`, `criterion_id`, `phase_id`
- `status` (`pass`, `needs_correction`, `not_assessable`)
- `measured_value` (nullable)
- `reference_value` (nullable)
- `confidence` (nullable)
- `correction_message_id`
- `evidence_summary` (non-image textual summary)

### `partner_classes` (P1)
- `id`, `partner_id`, `instructor_id`, `title`, `schedule_text`
- `city`, `public_venue`, `contact`, `trial_available`, `last_verified_at`
- `status`

### `content_permissions`
- `id`, `partner_id`, `asset_or_content_type`, `asset_or_content_id`
- `permission_scope`, `commercial_use_allowed`, `derivative_use_allowed`
- `expires_at`, `revocation_status`, `consent_evidence_ref`

### `consent_records`
- `id`, `user_id`, `consent_type`, `version`, `granted_at`, `revoked_at`
- `purpose`, `data_scope`

### `audit_logs`
- `id`, `actor_user_id`, `action`, `entity_type`, `entity_id`
- `before_summary`, `after_summary`, `created_at`, `request_id`

## 2. Key invariants

1. An assessment cannot exist without `movement_id`, `rubric_id`, and reference version.
2. `assessment_enabled` requires an approved rubric and approved reference asset.
3. A movement with `practice_mode != solo_beginner` cannot be enabled for unsupervised practice.
4. A content item cannot be public unless permission/access status permits it and review is approved.
5. A partner directory listing requires `public_listing_consent` and verified contact/location fields.
6. A result with insufficient data must have `status=not_assessable` and `overall_score=null`.
7. Historical scores keep the exact rubric/reference version used at the time.
8. Users can only access their own private practice results unless explicit instructor-sharing consent exists.
9. Partner admins cannot change permission/approval records outside their scope.
10. Revoked permission should unpublish or restrict the relevant assets according to the agreement.

## 3. Demo data rules

- Seed data must be marked `DEMO` and use clearly fictitious partner names only for local development.
- Never use a real school's name, logo, address, instructor, or class schedule without permission/verification.
- Do not put demo partners on production directory pages.
