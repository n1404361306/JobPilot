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
  name: string;
  description: string | null;
  content: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResumeTemplatePayload {
  name: string;
  description?: string | null;
  content: string;
  enabled?: boolean;
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
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface JobPayload {
  title: string;
  company: string;
  location?: string | null;
  salary_range?: string | null;
  source_url?: string | null;
  description?: string | null;
  status?: JobStatus;
}

export type ApplicationStatus = "pending" | "submitted" | "interview" | "offer" | "rejected" | "withdrawn";

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
