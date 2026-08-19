export interface EntityContext {
  entity_type: string;
  attributes: Record<string, unknown>;
  relationships: Record<string, unknown>[];
}

export interface Provenance {
  actor_id: string | null;
  actor_type: string | null;
  tenant_id: string | null;
  timestamp: string;
  source_artifact_ids: Record<string, string>;
  runtime: Record<string, unknown>;
}

export interface EvaluationResult {
  evaluation_id: string;
  vertical: string;
  entity_type: string;
  score: number | null;
  rule_results?: RuleResult[];
  violations: Violation[];
  required_actions: string[];
  provenance?: Provenance | null;
  /** Present when loaded from workspace / DB row. */
  created_at?: string;
  customer_id?: string | null;
}

export interface RuleResult {
  rule_id: string;
  control_key: string | null;
  obligation_key?: string | null;
  status: 'PASS' | 'PARTIAL' | 'FAIL' | 'NOT_APPLICABLE' | 'UNKNOWN';
  severity: string;
  description: string;
  recommended_actions: string[];
  source_fields: string[];
  evidence_ids: string[];
}

export interface Violation {
  rule_id: string;
  control_key?: string | null;
  obligation_key?: string | null;
  description: string;
  severity: string;
  recommended_actions: string[];
  source_fields?: string[];
  evidence_ids?: string[];
}

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  tenant_id: string | null;
  vertical: string;
  customer_id: string;
  agent_id: string;
  action: string;
  input_snapshot: Record<string, unknown>;
  output_snapshot: Record<string, unknown>;
  metadata: Record<string, unknown>;
  provenance?: Provenance | null;
}

export interface Document {
  document_id: string;
  vertical: string;
  format: string;
  content: string;
  provenance?: Provenance | null;
}

export interface VerticalInfo {
  id: string;
  name: string;
  description: string;
}

export interface JsonSchemaProperty {
  type: string;
  title: string;
  enum?: string[];
}

export interface OnboardingSchema {
  vertical: string;
  version: string;
  json_schema: {
    title?: string;
    type?: string;
    required?: string[];
    properties: Record<string, JsonSchemaProperty>;
  };
}

/** Founder-facing catalog from GET /verticals/{id}/questions */
export interface CatalogQuestion {
  key?: string | null;
  control_key?: string | null;
  obligation_key?: string | null;
  title: string;
  help?: string;
  type?: string;
  required?: boolean;
  options?: Record<string, string> | string[] | null;
  evidence_required?: boolean;
}

export interface ObligationCopy {
  title: string;
  description?: string;
}

export interface QuestionCatalog {
  vertical: string;
  version: string;
  profile: CatalogQuestion[];
  checklist: CatalogQuestion[];
  obligations: Record<string, ObligationCopy>;
}

export interface TemplateInfo {
  name: string;
  format: string;
}

export interface OnboardRequest {
  vertical: string;
  customer_id?: string;
  context: Record<string, unknown>;
}

export interface OnboardResponse {
  customer_id: string;
  vertical: string;
  status: string;
  provenance?: Provenance | null;
}

export interface EvaluateRequest {
  customer_id: string;
}

export interface GenerateDocRequest {
  customer_id: string;
  template_name: string;
  evaluation_id?: string;
  output_format?: string;
}

export interface TenantInfo {
  tenant_id: string;
  name: string;
  slug: string;
  status: string;
  roles: string[];
  auth_method: string;
  subject?: string;
}

export interface Tenant {
  tenant_id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
}

export interface TenantCreateRequest {
  name: string;
  slug?: string;
}

export interface ApiResponse<T> {
  data: T;
  meta: {
    request_id: string | null;
    version: string;
    timestamp: string;
  };
  error?: {
    code: string;
    message: string;
  } | null;
  pagination?: {
    page: number;
    page_size: number;
    total: number;
    next_cursor: string | null;
  } | null;
}

export interface Customer {
  customer_id: string;
  tenant_id: string;
  vertical: string;
  name: string;
  slug: string | null;
  status: 'draft' | 'onboarding' | 'active' | 'archived';
  context: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

export interface CustomerWorkspace {
  customer: Customer;
  obligations: Obligation[];
  controls: Control[];
  evidence: Evidence[];
  latest_evaluation: EvaluationResult | Record<string, unknown> | null;
  evaluation_count: number;
  document_count: number;
  audit_event_count: number;
  open_findings_count: number;
  latest_evaluation_id: string | null;
  latest_score: number | null;
  latest_activity_at: string | null;
}

export interface TimelineEvent {
  event_id: string;
  event_type: 'audit' | 'evaluation' | 'document';
  artifact_id: string;
  action: string;
  timestamp: string;
  actor_id: string | null;
  vertical: string | null;
  summary: string;
  links: Record<string, string>;
}

export interface CustomerCreateRequest {
  vertical: string;
  name: string;
  slug?: string;
  context?: Record<string, unknown>;
}

export interface CustomerUpdateRequest {
  name?: string;
  slug?: string;
  status?: 'draft' | 'onboarding' | 'active' | 'archived';
  context?: Record<string, unknown>;
}

export interface CustomerContextUpdateRequest {
  context: Record<string, unknown>;
}

export interface Finding {
  finding_id: string;
  tenant_id: string;
  customer_id: string;
  evaluation_id: string | null;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  status: 'open' | 'triaged' | 'assigned' | 'resolved' | 'closed';
  assignee: string | null;
  due_date: string | null;
  closure_evidence: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface FindingCreateRequest {
  customer_id: string;
  evaluation_id?: string;
  title: string;
  description?: string;
  severity: 'low' | 'medium' | 'high';
  status?: 'open' | 'triaged' | 'assigned' | 'resolved' | 'closed';
  assignee?: string;
  due_date?: string;
  closure_evidence?: Record<string, unknown>;
}

export interface FindingUpdateRequest {
  status?: 'open' | 'triaged' | 'assigned' | 'resolved' | 'closed';
  assignee?: string;
  due_date?: string;
  closure_evidence?: Record<string, unknown>;
  reason?: string;
}

export interface FindingsFilters {
  customer_id?: string;
  status?: string;
  severity?: string;
  assignee?: string;
  sort?: string;
  limit?: number;
}

export interface Task {
  task_id: string;
  tenant_id: string;
  customer_id: string;
  finding_id: string | null;
  title: string;
  assignee: string | null;
  due_date: string | null;
  status: 'todo' | 'in_progress' | 'awaiting_evidence' | 'done';
  created_at: string;
  updated_at: string;
}

export interface TaskCreateRequest {
  customer_id: string;
  finding_id?: string;
  title: string;
  assignee?: string;
  due_date?: string;
  status?: 'todo' | 'in_progress' | 'awaiting_evidence' | 'done';
}

export interface TaskUpdateRequest {
  title?: string;
  finding_id?: string | null;
  status?: 'todo' | 'in_progress' | 'awaiting_evidence' | 'done';
  assignee?: string;
  due_date?: string;
  reason?: string;
}


export interface TasksFilters {
  customer_id?: string;
  finding_id?: string;
  status?: string;
  assignee?: string;
  sort?: string;
  limit?: number;
}

export interface DocumentVersion {
  version_id: string;
  document_id: string;
  tenant_id: string;
  customer_id: string;
  version_number: number;
  status: 'generated' | 'reviewed' | 'approved' | 'published' | 'superseded';
  content: string;
  reviewed_by: string | null;
  approved_by: string | null;
  regenerated_from: string | null;
  superseded_by: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentsFilters {
  customer_id?: string;
  status?: string;
  limit?: number;
}

export interface DocumentRegenerateRequest {
  content?: string;
}

export interface ApiKey {
  api_key_id: string;
  tenant_id: string;
  roles: string[];
  expires_at: string | null;
  revoked: boolean;
  created_at: string;
}

export interface ApiKeyCreate {
  api_key_id: string;
  roles: string[];
  expires_at?: string;
}

export interface ApiKeySecret {
  api_key_id: string;
  secret: string;
}

export interface TenantDetails {
  tenant_id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
}

export interface TenantUpdate {
  name?: string;
  slug?: string;
  status?: string;
}

export interface TenantMembership {
  membership_id: string;
  subject: string;
  tenant_id: string;
  role: string;
  revoked: boolean;
  created_at: string;
}

export interface TenantMembershipCreate {
  subject: string;
  role: string;
}

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Job {
  job_id: string;
  tenant_id: string;
  job_type: string;
  status: JobStatus;
  retry_count: number;
  max_retries: number;
  last_error: string | null;
  result: Record<string, unknown> | null;
  payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export type SystemEventSeverity = 'high' | 'medium' | 'low';

export interface SystemEvent {
  event_id: string;
  event_type: string;
  severity: SystemEventSeverity;
  message: string;
  occurred_at: string;
  artifact_id: string | null;
  link: string | null;
}

export interface Obligation {
  obligation_id: string;
  tenant_id: string;
  customer_id: string;
  obligation_key: string | null;
  rule_id: string | null;
  name: string;
  description: string;
  status: string;
  linked_finding_id: string | null;
  linked_document_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ObligationCreateRequest {
  name: string;
  description?: string;
  status?: string;
  linked_finding_id?: string;
  linked_document_id?: string;
}

export interface ObligationUpdateRequest {
  name?: string;
  description?: string;
  status?: string;
  linked_finding_id?: string;
  linked_document_id?: string;
}

export type ControlAnswer = 'unanswered' | 'yes' | 'no' | 'not_sure';

export interface Control {
  control_id: string;
  tenant_id: string;
  customer_id: string;
  control_key: string | null;
  rule_id: string | null;
  obligation_key: string | null;
  name: string;
  description: string;
  answer: ControlAnswer;
  owner: string | null;
  last_reviewed_at: string | null;
  status: string;
  linked_obligation_id: string | null;
  linked_finding_id: string | null;
  linked_document_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ControlCreateRequest {
  name: string;
  description?: string;
  status?: string;
  linked_obligation_id?: string;
  linked_finding_id?: string;
  linked_document_id?: string;
}

export interface ControlUpdateRequest {
  answer?: ControlAnswer;
  owner?: string | null;
  last_reviewed_at?: string | null;
}

export interface Evidence {
  evidence_id: string;
  tenant_id: string;
  customer_id: string;
  control_id: string;
  name: string;
  type: string;
  uri: string;
  verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface EvidenceCreateRequest {
  control_id: string;
  name: string;
  type?: string;
  uri: string;
}

export interface EvidenceUpdateRequest {
  control_id?: string;
  name?: string;
  type?: string;
  uri?: string;
}
