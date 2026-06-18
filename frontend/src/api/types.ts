export interface ApiEnvelope<T> {
  code: number;
  message: string;
  data: T;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface Resume {
  id: number;
  user_id: number;
  title: string;
  content: string;
  file_url: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResumePayload {
  title: string;
  content: string;
  file_url?: string | null;
  is_default?: boolean;
}

export interface ResumeTemplate {
  id: number;
  user_id: number | null;
  name: string;
  description: string | null;
  content: string;
  enabled: boolean;
  is_system: boolean;
  is_public: boolean;
  copied_from_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface ResumeTemplatePayload {
  name: string;
  description?: string | null;
  content: string;
  enabled?: boolean;
  is_public?: boolean;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ResumeTemplateChatPayload {
  message: string;
  history?: ChatMessage[];
  current_template?: string | null;
}

export type JobStatus = "active" | "closed" | "archived";

export interface Job {
  id: number;
  user_id: number;
  title: string;
  company: string;
  location: string | null;
  salary_range: string | null;
  source_url: string | null;
  source_type: string | null;
  job_type: string | null;
  deadline: string | null;
  tags: string | null;
  is_favorite: boolean;
  import_batch_id: string | null;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface JobBatchImportResult {
  batch_id: string;
  count: number;
  jobs: Job[];
}

export interface JobBatchPreviewResult {
  count: number;
  jobs: JobPayload[];
}

export interface JobPayload {
  title: string;
  company: string;
  location?: string | null;
  salary_range?: string | null;
  source_url?: string | null;
  source_type?: string | null;
  job_type?: string | null;
  deadline?: string | null;
  tags?: string | null;
  is_favorite?: boolean;
  import_batch_id?: string | null;
  description?: string | null;
  status?: JobStatus;
}

export interface ResumeVersion {
  id: number;
  resume_id: number;
  user_id: number;
  version_name: string;
  content: string;
  structured_data: string | null;
  created_at: string;
  updated_at: string;
}

export type ApplicationStatus =
  | "pending"
  | "submitted"
  | "screening"
  | "written"
  | "tech_first"
  | "tech_second"
  | "hr_interview"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

export interface Application {
  id: number;
  user_id: number;
  job_id: number;
  resume_id: number | null;
  status: string;
  channel: string | null;
  note: string | null;
  applied_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationPayload {
  job_id?: number;
  resume_id?: number | null;
  status?: ApplicationStatus;
  channel?: string | null;
  note?: string | null;
  applied_at?: string | null;
}

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface AiLog {
  id: number;
  user_id: number | null;
  model_name: string | null;
  prompt_type: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_estimate: number | null;
  status: string | null;
  error_message: string | null;
  duration_ms: number | null;
  created_at: string | null;
}

export interface OcrLog {
  id: number;
  source_type: string | null;
  result_summary: string | null;
}

export interface SystemLog {
  id: number;
  level: string;
  message: string;
}

export interface SystemConfig {
  key: string;
  value: string;
}

export interface MatchReport {
  id: number;
  user_id: number;
  resume_id: number;
  job_id: number;
  score: number;
  summary: string;
  strengths: string | null;
  gaps: string | null;
  suggestions: string | null;
  created_at: string;
}

export interface StatisticsOverview {
  resume_count: number;
  job_count: number;
  active_job_count?: number;
  application_count: number;
  match_report_count: number;
  average_match_score: number;
  status_counts: Record<string, number>;
  city_counts: Record<string, number>;
}

export interface StatisticsApplications {
  total: number;
  status_counts: Record<string, number>;
  interview_count?: number;
  offer_count?: number;
  interview_conversion_rate: number;
  offer_conversion_rate: number;
}

export interface StatisticsJobs {
  total: number;
  active_count?: number;
  source_counts: Record<string, number>;
  type_counts: Record<string, number>;
  city_counts: Record<string, number>;
  favorite_count: number;
  tag_counts: Record<string, number>;
}

export interface StatisticsMatches {
  total: number;
  average_score: number;
  score_ranges: Record<string, number>;
  latest: MatchReport[];
}

export interface Report {
  id: number;
  user_id: number;
  title: string;
  content: string;
  report_type: string;
  created_at: string;
}

export interface AIResult {
  title: string;
  content: string;
  data: Record<string, unknown>;
}

export interface DeliveryProfile {
  id: number;
  user_id: number;
  real_name: string | null;
  phone: string | null;
  email: string | null;
  school: string | null;
  major: string | null;
  common_answers: string | null;
  created_at: string;
  updated_at: string;
}

export interface DeliveryTask {
  id: number;
  user_id: number;
  job_id: number;
  resume_id: number | null;
  site_name: string | null;
  target_url: string | null;
  task_status: string;
  preview_data: string | null;
  created_at: string;
  updated_at: string;
}

export interface DeliveryTaskLog {
  id: number;
  task_id: number;
  user_id: number;
  level: string;
  message: string;
  created_at: string;
}

export interface PromptTemplate {
  id: number;
  template_code: string;
  template_name: string;
  template_content: string;
  version: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface DeliverySite {
  site_name: string;
  login_url?: string | null;
  enabled: boolean;
  rate_limit_note?: string | null;
}
