import type { EvaluationResult } from '@/types';

export interface MindStatus {
  mind_row_id: string;
  mind_id: string;
  mind_email: string | null;
  status: string;
  last_interaction_at: string | null;
  memory_version: string | null;
  configured: boolean;
}

export interface Author {
  author_id: string;
  customer_id: string;
  tenant_id: string;
  name: string;
  status: string;
  vertical: string;
  context: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  mind: MindStatus | null;
}

export interface Book {
  id: string;
  author_id: string;
  working_title: string;
  final_title: string | null;
  subtitle: string | null;
  series_name: string | null;
  description: string;
  status: string;
  publication_strategy: string;
  created_at: string;
  updated_at: string;
}

export interface Edition {
  id: string;
  book_id: string;
  format: string;
  isbn: string | null;
  language: string;
  trim_size: string | null;
  page_count: number | null;
  interior_file_uri: string | null;
  cover_file_uri: string | null;
  list_price: number | null;
  currency: string;
  publication_date: string | null;
  platform_strategy: Record<string, unknown>;
  publishing_status: string;
  proof_review_status: string;
  created_at: string;
  updated_at: string;
}

export interface SourceDocument {
  id: string;
  book_id: string;
  file_uri: string;
  file_name: string;
  mime_type: string;
  sha256: string;
  extracted_text: string;
  rights_declaration: string;
  version: number;
  created_at: string;
}

export interface Asset {
  id: string;
  book_id: string;
  source_document_id: string | null;
  parent_asset_id: string | null;
  type: string;
  platform: string;
  content: string;
  source_references: Record<string, unknown>[];
  assumptions: string[];
  call_to_action: string;
  risk_notes: string[];
  governance_status: string;
  approval_status: string;
  author_correction: string | null;
  applied_preference: boolean;
  evaluation: EvaluationResult | null;
  created_at: string;
}

export interface CampaignTask {
  id: string;
  campaign_id: string;
  asset_id: string | null;
  channel: string;
  phase: string;
  scheduled_for: string | null;
  approval_status: string;
  execution_status: string;
}

export interface Campaign {
  id: string;
  book_id: string;
  campaign_type: string;
  launch_date: string | null;
  timezone: string;
  status: string;
  tasks: CampaignTask[];
}

export interface JobStatus {
  job_id: string;
  status: string;
  last_error: string | null;
  result: Record<string, unknown> | null;
}
