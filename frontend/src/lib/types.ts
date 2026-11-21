/** Kontrak tipe API (selaras dengan backend/app/schemas/*, lihat /docs OpenAPI). */

export type Role = "learner" | "instructor" | "curator" | "admin";
export type ContentStatus =
  | "draft" | "pending_review" | "needs_revision" | "rejected" | "verified" | "published" | "archived";

export interface User { id: string; email: string; display_name: string; role: Role }
export interface AuthPayload { user: User; csrf_token: string }

export interface Page<T> { items: T[]; page: number; page_size: number; total: number; total_pages: number }

export interface Provenance {
  status: ContentStatus; is_demo: boolean; partner_verified: boolean; verification_label: string;
  source_citation: string | null; source_url: string | null;
  approved_by_name: string | null; approved_at: string | null;
  /** ADR-0008: source_backed | official_curriculum | partner_restricted */
  content_basis?: ContentBasis | null; attribution?: string | null;
}
export type ContentBasis = "source_backed" | "official_curriculum" | "partner_restricted";

export interface TraditionSummary {
  id: string; slug: string; name: string; local_name: string | null; region: string | null;
  public_summary: string | null; content_basis?: ContentBasis; provenance: Provenance;
}
export interface PartnerSummary {
  id: string; slug: string; name: string; partner_type: string; region: string | null;
  city: string | null; official_description: string | null; provenance: Provenance;
}
export interface InstructorOut {
  id: string; slug: string; name: string; bio: string | null; preferred_attribution: string | null;
  partner_slug: string | null; provenance: Provenance;
}
export interface MovementSummary {
  id: string; slug: string; name_id: string; name_local: string | null; practice_mode: string;
  assessment_enabled: boolean; tradition_slug: string | null; tradition_name?: string | null;
  partner_slug?: string | null; partner_name?: string | null; partner_verified?: boolean;
  level?: Level | null; safety_category?: SafetyCategory | null; version_no?: number | null;
  content_basis?: ContentBasis; provenance: Provenance;
}
export interface MovementOut extends MovementSummary {
  description: string | null; safety_notes: string | null; document?: PublicDocument | null;
}
export interface CourseSummary {
  id: string; slug: string; title: string; summary: string | null; level: string;
  estimated_minutes: number | null; tradition_slug: string | null; tradition_name: string | null;
  partner_slug: string | null; partner_name: string | null; lesson_count: number; content_basis?: ContentBasis; provenance: Provenance;
}
export interface LessonRef {
  id: string; slug: string; title: string; order_index: number; estimated_minutes: number | null;
  completed: boolean | null;
}
export interface ModuleOut { id: string; title: string; summary: string | null; order_index: number; lessons: LessonRef[] }
export interface Progress { completed: number; total: number; percent: number }
export interface EnrollmentState {
  status: "active" | "completed" | "dropped"; enrolled_at: string; completed_at: string | null;
  progress: Progress; last_lesson_slug: string | null; next_lesson_slug: string | null;
}
export interface CourseDetail extends CourseSummary {
  safety_notes: string | null; instructor: InstructorOut | null; modules: ModuleOut[];
  enrollment: EnrollmentState | null;
}
export interface TraditionDetail extends TraditionSummary {
  access_scope: string; partners: PartnerSummary[]; courses: CourseSummary[]; movements: MovementSummary[];
}
export interface PartnerDetail extends PartnerSummary {
  traditions: TraditionSummary[]; instructors: InstructorOut[]; courses: CourseSummary[];
}
export interface MaterialOut {
  id: string; kind: "text" | "link"; title: string; content: string | null; url: string | null;
  attribution_text: string;
}
export interface LessonDetail {
  id: string; slug: string; title: string; objective: string | null; body: string | null;
  safety_notes: string | null; estimated_minutes: number | null; module_title: string;
  course: CourseSummary; movement: MovementOut | null; materials: MaterialOut[];
  prev_lesson: LessonRef | null; next_lesson: LessonRef | null; provenance: Provenance;
  enrolled: boolean; lesson_status: "in_progress" | "completed" | null; practice: LessonPractice;
}
export interface MyEnrollment { course: CourseSummary; enrollment: EnrollmentState }
export interface MyProgress { enrollments: MyEnrollment[]; totals: Progress; courses_completed: number }
export interface ProgressUpdate { lesson_id: string; status: string; completed_at: string | null; enrollment: EnrollmentState }

export interface ManageItem {
  id: string; kind: string; slug: string; title: string; status: ContentStatus; is_demo: boolean;
  updated_at: string; created_by_user_id: string | null;
}
export interface HistoryEntry { action: string; actor: string | null; detail: Record<string, unknown> | null; created_at: string }
export interface ManageDetail {
  kind: string; fields: Record<string, unknown> & { id: string; status: ContentStatus; slug: string };
  allowed_actions: string[]; can_edit: boolean; history: HistoryEntry[];
  modules?: Record<string, unknown>[]; materials?: Record<string, unknown>[];
}
export interface AdminUser { id: string; email: string; display_name: string; role: Role; status: string; created_at: string }

export interface ApiErrorBody {
  code: string; message: string; details?: unknown; request_id?: string | null;
}

/** ---- Practice Studio (kontrak: docs/PRACTICE_STUDIO_CONTRACT.md). Hanya metadata + agregat; tanpa landmark/frame. ---- */
export interface LessonPractice { available: boolean; reason: string | null; is_demo: boolean; label: string }
export type DetectionStateKey = "waiting_for_subject" | "detecting" | "partial_detection" | "insufficient_visibility";
export interface QualitySummaryPayload {
  frames_total: number; processed_frames: number; dropped_frames: number; valid_frame_ratio: number;
  ms_in_state: Record<DetectionStateKey, number>;
  reasons: Record<"NO_POSE" | "MULTIPLE_PEOPLE" | "TOO_FEW_LANDMARKS" | "LOW_VISIBILITY" | "OUT_OF_FRAME" | "NO_HAND" | "LOW_HAND_CONFIDENCE", number>;
  engine: "worker" | "synthetic"; delegate: "GPU" | "CPU" | null; simulated: boolean;
}
export type PracticeStatus = "in_progress" | "completed" | "abandoned" | "error";
export interface PracticeLessonBrief {
  id: string; slug: string; title: string; course_slug: string; course_title: string; is_demo: boolean; verification_label: string;
}
export interface PracticeSession {
  id: string; status: PracticeStatus; started_at: string; ended_at: string | null;
  active_duration_ms: number | null; paused_duration_ms: number | null; model_version: string; client_version: string | null;
  quality_summary: QualitySummaryPayload | null; error_code: string | null; lesson: PracticeLessonBrief;
}
export interface PracticeDayPoint { date: string; sessions: number; active_seconds: number }
export interface PracticeSummary {
  total_sessions: number; completed_sessions: number; total_active_seconds: number;
  sessions_last_7_days: number; active_seconds_last_7_days: number; days: PracticeDayPoint[]; last_session: PracticeSession | null;
}


// ============ Instructor & Partner Studio (docs/INSTRUCTOR_PARTNER_CONTRACT.md) ============
export type Level = "beginner" | "intermediate" | "advanced";
export type SafetyCategory = "solo_beginner" | "supervised_practice" | "contact_practice" | "weapon_related" | "restricted";
export type LicenseType = "instructor_owned" | "partner_permission" | "other_written_permission";
export type PartnerVerification = "draft" | "pending_verification" | "verified" | "rejected" | "suspended";
export type PartnerAction = "submit" | "verify" | "reject" | "suspend" | "reopen" | "reinstate" | "publish_listing" | "unlist";
export type DocAction = "submit" | "curator_review" | "confirm_partner" | "request_revision" | "reject" | "approve" | "publish" | "archive";

export interface PublicPhase {
  id: string; order_index: number; name: string; instruction: string; body_focus: string[];
  safety_note: string | null; start_ms: number | null; end_ms: number | null;
}
export interface PublicMedia {
  id: string; kind: "video" | "image"; title: string; url: string; rights_holder: string;
  source_description: string; usage_scope: string; is_demo: boolean;
}
export interface PublicDocument {
  id: string; version_no: number; name_id: string; name_local: string | null; level: Level | null;
  safety_category: SafetyCategory | null; prerequisites: string | null; learning_context: string | null;
  description: string | null; terminology_notes: string | null; common_mistakes: string[];
  safety_guidance: string | null; relevant_body_parts: string[]; relevant_landmarks: number[];
  phases: PublicPhase[]; media: PublicMedia[]; rights_holder: string | null; license_type: LicenseType | null;
  usage_scope: string | null; changelog: string | null; published_at: string | null; authors: string[];
}
export interface PublicVersion { version_no: number; status: string; changelog: string | null; published_at: string | null; is_current: boolean }

export interface PartnerRow {
  id: string; slug: string; name: string; partner_type: string; region: string | null; city: string | null;
  verification_status: PartnerVerification; verification_label: string; is_demo: boolean;
  listed_publicly: boolean; my_role: "manager" | "instructor" | null; updated_at: string;
}
export interface PartnerMember { user_id: string; name: string; email: string; role: "manager" | "instructor"; user_role: Role }
export interface PartnerDoc { id: string; kind: string; description: string | null; filename: string; mime: string; size_bytes: number; sha256: string; created_at: string }
export interface Readiness { key: string; label: string; ok: boolean }
export interface StudioPartnerDetail extends PartnerRow {
  official_description: string | null; responsible_name: string | null; responsible_role: string | null;
  responsible_contact: string | null; contact_email: string | null; contact_phone: string | null;
  public_listing_consent: boolean; verification_note: string | null; approval_evidence_ref: string | null;
  verification_decided_by: string | null; verification_decided_at: string | null; submitted_at: string | null;
  members: PartnerMember[]; traditions: { id: string; slug: string; name: string }[]; documents: PartnerDoc[];
  readiness: Readiness[]; allowed_actions: PartnerAction[]; can_edit_profile: boolean; can_manage: boolean;
}
export interface PartnerEvent { action: string; from_status: string | null; to_status: string; actor: string | null; note: string | null; evidence_ref: string | null; created_at: string }

export interface StudioPhase {
  id?: string; order_index?: number; name: string; instruction: string; body_focus: string[];
  safety_note: string | null; start_ms: number | null; end_ms: number | null;
}
export interface StudioDocument {
  id: string; version_no: number; status: ContentStatus; status_label: string; is_demo: boolean; legacy_import: boolean;
  review_note: string | null; created_at: string; updated_at: string; published_at: string | null; approved_at: string | null;
  approval_evidence_ref: string | null; partner_confirmation_note: string | null;
  curator_reviewed_at: string | null; partner_confirmed_at: string | null;
  name_id: string; name_local: string | null; level: Level | null; safety_category: SafetyCategory | null;
  prerequisites: string | null; learning_context: string | null; description: string | null;
  terminology_notes: string | null; common_mistakes: string[]; safety_guidance: string | null;
  relevant_body_parts: string[]; relevant_landmarks: number[]; source_citation: string | null; source_url: string | null;
  author_declaration: boolean; rights_holder: string | null; license_type: LicenseType | null; usage_scope: string | null;
  changelog: string | null;
  phases: StudioPhase[]; author: string | null; approved_by: string | null;
  curator_reviewed_by: string | null; partner_confirmed_by: string | null;
  completeness: Readiness[]; complete: boolean; editable: boolean; allowed_actions: DocAction[]; is_author: boolean;
}
export interface StudioMovementRow {
  id: string; slug: string; name_id: string; name_local: string | null; tradition_id: string; tradition_name: string | null;
  partner_id: string; partner_name: string | null; level: Level | null; safety_category: SafetyCategory | null;
  is_demo: boolean; working_version: number | null; working_status: ContentStatus | null;
  working_status_label: string | null; working_document_id: string | null; published_version_no: number | null;
  published: boolean; updated_at: string;
}
export interface StudioVersion {
  id: string; version_no: number; status: ContentStatus; status_label: string; changelog: string | null;
  author: string | null; published_at: string | null; created_at: string; is_current: boolean;
}
export interface LinkedLesson { id: string; title: string; slug: string; status: ContentStatus; course_slug: string; course_title: string }
export interface StudioMovement extends StudioMovementRow {
  active_document: StudioDocument | null; versions: StudioVersion[]; lessons: LinkedLesson[];
  can_create_version: boolean; media_count: number; annotation_count: number; practice_eligible: boolean;
}
export interface LinkableLesson { id: string; title: string; course_title: string; status: ContentStatus; linked: boolean }
export interface HistoryEntry { action: string; actor: string | null; detail: Record<string, unknown> | null; created_at: string }

export interface StudioMedia {
  id: string; kind: "video" | "image"; title: string; filename: string; mime: string; size_bytes: number; sha256: string;
  rights_holder: string; source_description: string; license_type: LicenseType; usage_scope: string;
  consent_status: "declared" | "verified" | "rejected" | "revoked"; consent_label: string;
  permission_evidence_ref: string | null; access_level: "private" | "reviewers" | "public";
  retention_until: string | null; uploader: string | null; is_demo: boolean; created_at: string; url: string;
  can_decide: boolean; can_delete: boolean;
}
export interface InstructorAnnotation {
  id: string; movement_id: string; media_id: string | null; fixture_key: "demo-synthetic" | null; phase_id: string | null;
  kind: "phase_marker" | "note"; timestamp_ms: number; label: string; note: string | null; annotator: string | null;
  annotator_user_id: string | null; model_version: string | null; source_note: string | null;
  review_status: "pending" | "accepted" | "rejected"; reviewed_by: string | null; reviewed_at: string | null;
  created_at: string; provenance_label: string;
}

export interface DashboardAttention {
  kind: string; label: string; title: string; since: string | null; note: string | null;
  movement_id?: string; document_id?: string; partner_id?: string; version_no?: number;
}
export interface StudioDashboard {
  role: Role; partners: PartnerRow[]; attention: DashboardAttention[];
  counts: { movements: number; documents_by_status: Record<string, number>; published_movements: number; media_awaiting_consent: number; lessons_linked: number };
  tradition_coverage: { tradition_id: string; tradition_name: string | null; total: number; published: number }[];
  recent_activity: { action: string; actor: string | null; detail: Record<string, unknown> | null; entity_type: string; entity_id: string; created_at: string }[];
}

// ============ Pilot & Impact Studio (docs/PILOT_STUDIO_CONTRACT.md) ============
export type ProgramStatus = "draft" | "pending_approval" | "approved" | "active" | "completed" | "cancelled" | "archived";
export type ProgramAction = "submit" | "approve" | "reject" | "activate" | "complete" | "cancel" | "archive";
export interface CohortSessionOut { id: string; title: string; starts_at: string; ends_at: string | null; location_note: string | null }
export interface CohortOut {
  id: string; program_id: string; name: string; course_id: string; course_title: string | null; instructor_user_id: string | null;
  instructor: string | null; status: "draft" | "open" | "closed" | "completed"; start_date: string | null; end_date: string | null;
  capacity: number; member_count: number; sessions: CohortSessionOut[];
}
export interface AnnouncementOut { id: string; title: string; body: string; cohort_id: string | null; author: string | null; created_at: string }
export interface ProgramRow {
  id: string; name: string; partner_id: string; partner_name: string | null; partner_verified: boolean; status: ProgramStatus; status_label: string;
  is_demo: boolean; start_date: string | null; end_date: string | null; capacity: number; responsible: string | null; official: boolean;
  official_note: string; updated_at: string; cohort_count: number; member_count: number;
}
export interface ProgramDetail extends ProgramRow {
  objective: string | null; description: string | null; responsible_user_id: string | null; default_course_id: string | null; review_note: string | null;
  approved_by: string | null; approved_at: string | null; approval_evidence_ref: string | null; allowed_actions: ProgramAction[]; submit_missing: string[];
  cohorts: CohortOut[]; announcements: AnnouncementOut[]; retention_days: number; anonymized_at: string | null;
}
export interface InvitationOut { id: string; email: string | null; status: "pending" | "accepted" | "revoked" | "expired"; expires_at: string; accepted_at: string | null; revoked_at: string | null; created_at: string; token?: string; token_note?: string }
export interface CohortManage extends CohortOut {
  program: ProgramRow; members: { user_id: string; name: string; email: string; status: string; joined_at: string }[]; invitations: InvitationOut[];
}
export interface InvitePreview {
  status: InvitationOut["status"]; program_name: string; cohort_name: string; partner_name: string; is_demo: boolean; program_status: ProgramStatus;
  program_status_label: string; start_date: string | null; end_date: string | null; expires_at: string; email_bound: boolean; joinable: boolean;
}
export interface SurveyQuestion { id: string; type: "single_choice" | "rating" | "open_text"; text: string; required: boolean; options?: string[] | null; scale_min?: number; scale_max?: number; min_label?: string | null; max_label?: string | null }
export interface SurveyOut { id: string; program_id: string; kind: string; title: string; status: "draft" | "open" | "closed"; questions: SurveyQuestion[]; instrument_note: string; responses: number | null; answered?: boolean }
export interface PortalMembership { cohort_id: string; cohort_name: string; program_id: string; program_name: string; program_status: ProgramStatus; program_status_label: string; is_demo: boolean; course_slug: string | null; course_title: string | null; joined_at: string; progress: { completed: number; total: number; percent: number } | null }
export interface Portal { memberships: PortalMembership[]; pending_surveys: SurveyOut[] }
export interface MyCohort extends CohortOut {
  program_name: string; program_objective: string | null; program_status_label: string; is_demo: boolean; partner_name: string; course_slug: string | null;
  lessons: { id: string; slug: string; title: string; module: string; completed: boolean }[]; progress: { completed: number; total: number; percent: number } | null;
  practice: { completed_sessions: number; active_minutes: number }; announcements: AnnouncementOut[]; consents: { research_aggregate: boolean; publication_quote: boolean };
  surveys: SurveyOut[]; policy_version: string;
}
export interface UsageCohort {
  cohort_id: string; cohort_name: string; active_members: number; lessons_total: number; suppressed: boolean; completion_rate: number | null; lessons_completed: number | null;
  active_participants: number | null; active_rate?: number | null; note?: string;
  practice: { sessions: number; by_status: Record<string, number>; active_minutes: number; sessions_per_active_participant: number | null } | null;
}
export interface SurveyQuestionStat { id: string; text: string; type: string; answered: number; distribution?: Record<string, number>; mean?: number | null }
export interface SurveyStat { survey_id: string; kind: string; title: string; status: string; responses: number; eligible: number; response_rate: number | null; instrument_note: string; suppressed: boolean; note?: string; questions: SurveyQuestionStat[] }
export interface ProgramAnalytics {
  program: { id: string; name: string; status: string; is_demo: boolean }; filters: Record<string, string | null>; min_respondents: number; disclaimer: string; generated_at: string;
  enrollment: { cohorts: { cohort_id: string; cohort_name: string; capacity: number; active: number; withdrawn: number; removed: number; status: string }[]; invitations: Record<string, number>; active_total: number; capacity_total: number };
  usage: { cohorts: UsageCohort[]; retention: { cohort_id: string; suppressed: boolean; weeks: { week: number; active: number; rate: number }[] }[] };
  surveys: SurveyStat[]; consent: { members: number; research_aggregate: number | null; publication_quote: number | null };
}
export interface CohortDashboard {
  cohort: CohortOut; program: { id: string; name: string; status: string }; disclaimer: string; thresholds: { no_start_days: number; inactive_days: number };
  summary: { members: number; not_started: number; needs_attention: number; lessons_total: number; completed_all: number };
  participants: { user_id: string; name: string; joined_at: string; started: boolean; last_activity_at: string | null; lessons_completed: number; lessons_total: number; completion: number | null; practice_sessions: number; practice_minutes: number; needs_attention: boolean; attention_reasons: string[]; surveys_pending: number }[];
}
