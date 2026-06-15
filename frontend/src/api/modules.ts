import { http } from "./http";
import type {
  AdminUser,
  AiLog,
  Application,
  ApplicationPayload,
  Job,
  JobPayload,
  OcrLog,
  Resume,
  ResumePayload,
  ResumeTemplate,
  ResumeTemplatePayload,
  SystemConfig,
  SystemLog,
  TokenResponse,
  UserProfile
} from "./types";

export const authApi = {
  register(payload: { username: string; email: string; password: string }) {
    return http.post<unknown, { id: number }>("/auth/register", payload);
  },
  login(payload: { username: string; password: string }) {
    return http.post<unknown, TokenResponse>("/auth/login", payload);
  },
  logout() {
    return http.post<unknown, null>("/auth/logout");
  },
  me() {
    return http.get<unknown, UserProfile>("/auth/me");
  }
};

export const resumeApi = {
  list() {
    return http.get<unknown, Resume[]>("/resumes");
  },
  create(payload: ResumePayload) {
    return http.post<unknown, Resume>("/resumes", payload);
  },
  get(id: number) {
    return http.get<unknown, Resume>(`/resumes/${id}`);
  },
  update(id: number, payload: Partial<ResumePayload>) {
    return http.put<unknown, Resume>(`/resumes/${id}`, payload);
  },
  remove(id: number) {
    return http.delete<unknown, null>(`/resumes/${id}`);
  }
};

export const templateApi = {
  list() {
    return http.get<unknown, ResumeTemplate[]>("/resume-templates");
  },
  manage() {
    return http.get<unknown, ResumeTemplate[]>("/resume-templates/manage");
  },
  create(payload: ResumeTemplatePayload) {
    return http.post<unknown, ResumeTemplate>("/resume-templates", payload);
  },
  update(id: number, payload: Partial<ResumeTemplatePayload>) {
    return http.put<unknown, ResumeTemplate>(`/resume-templates/${id}`, payload);
  },
  remove(id: number) {
    return http.delete<unknown, null>(`/resume-templates/${id}`);
  }
};

export const jobApi = {
  list(params?: { status?: string; keyword?: string }) {
    return http.get<unknown, Job[]>("/jobs", { params });
  },
  create(payload: JobPayload) {
    return http.post<unknown, Job>("/jobs", payload);
  },
  get(id: number) {
    return http.get<unknown, Job>(`/jobs/${id}`);
  },
  update(id: number, payload: Partial<JobPayload>) {
    return http.put<unknown, Job>(`/jobs/${id}`, payload);
  },
  remove(id: number) {
    return http.delete<unknown, null>(`/jobs/${id}`);
  }
};

export const applicationApi = {
  list(params?: { status?: string }) {
    return http.get<unknown, Application[]>("/applications", { params });
  },
  create(payload: Required<Pick<ApplicationPayload, "job_id">> & ApplicationPayload) {
    return http.post<unknown, Application>("/applications", payload);
  },
  get(id: number) {
    return http.get<unknown, Application>(`/applications/${id}`);
  },
  update(id: number, payload: ApplicationPayload) {
    return http.put<unknown, Application>(`/applications/${id}`, payload);
  },
  remove(id: number) {
    return http.delete<unknown, null>(`/applications/${id}`);
  }
};

export const adminApi = {
  users() {
    return http.get<unknown, AdminUser[]>("/admin/users");
  },
  updateUserStatus(id: number, is_active: boolean) {
    return http.put<unknown, null>(`/admin/users/${id}/status`, { is_active });
  },
  aiLogs() {
    return http.get<unknown, AiLog[]>("/admin/ai-logs");
  },
  ocrLogs() {
    return http.get<unknown, OcrLog[]>("/admin/ocr-logs");
  },
  systemLogs() {
    return http.get<unknown, SystemLog[]>("/admin/system-logs");
  },
  systemConfigs() {
    return http.get<unknown, SystemConfig[]>("/admin/system-configs");
  },
  updateSystemConfig(key: string, config_value: string) {
    return http.put<unknown, null>(`/admin/system-configs/${key}`, { config_value });
  }
};
