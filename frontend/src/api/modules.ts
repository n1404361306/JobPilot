import { http } from "./http";
import type {
  AdminUser,
  AIResult,
  AiLog,
  Application,
  ApplicationPayload,
  DeliveryProfile,
  DeliverySite,
  DeliveryTask,
  DeliveryTaskLog,
  Job,
  JobBatchImportResult,
  JobBatchPreviewResult,
  JobPayload,
  MatchReport,
  OcrLog,
  PromptTemplate,
  Report,
  Resume,
  ResumePayload,
  ResumeTemplate,
  ResumeTemplatePayload,
  ResumeTemplateChatPayload,
  ResumeVersion,
  StatisticsApplications,
  StatisticsJobs,
  StatisticsMatches,
  StatisticsOverview,
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
  },
  versions(id: number) {
    return http.get<unknown, ResumeVersion[]>(`/resumes/${id}/versions`);
  },
  createVersion(id: number, payload: { version_name: string; content: string; structured_data?: string | null }) {
    return http.post<unknown, ResumeVersion>(`/resumes/${id}/versions`, payload);
  },
  selectTemplate(id: number, templateId: string) {
    return http.post<unknown, Resume>(`/resumes/${id}/template`, { template_id: templateId });
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
  },
  copy(id: number) {
    return http.post<unknown, ResumeTemplate>(`/resume-templates/${id}/copy`);
  },
  get(id: number) {
    return http.get<unknown, ResumeTemplate>(`/resume-templates/${id}`);
  },
  upload(file: File, payload?: { name?: string; description?: string; is_public?: boolean }) {
    const data = new FormData();
    data.append("file", file);
    if (payload?.name) data.append("name", payload.name);
    if (payload?.description) data.append("description", payload.description);
    data.append("is_public", String(payload?.is_public ?? false));
    return http.post<unknown, ResumeTemplate>("/resume-templates/upload", data);
  },
  createMine(payload: ResumeTemplatePayload) {
    return http.post<unknown, ResumeTemplate>("/resume-templates/mine", payload);
  },
  updateMine(id: number, payload: Partial<ResumeTemplatePayload>) {
    return http.put<unknown, ResumeTemplate>(`/resume-templates/${id}/mine`, payload);
  }
};

export const jobApi = {
  list(params?: { status?: string; keyword?: string; favorite?: boolean }) {
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
  },
  importText(payload: { text: string; source_url?: string | null }) {
    return http.post<unknown, Job>("/jobs/import/text", payload);
  },
  previewBatchText(payload: { text: string; separator?: string | null }) {
    return http.post<unknown, JobBatchPreviewResult>("/jobs/import/batch-text/preview", payload, { timeout: 120000 });
  },
  importBatchText(payload: { jobs: JobPayload[] }) {
    return http.post<unknown, JobBatchImportResult>("/jobs/import/batch-text", payload, { timeout: 120000 });
  },
  importUrl(payload: { source_url: string; text?: string | null }) {
    return http.post<unknown, Job>("/jobs/import/url", payload, { timeout: 120000 });
  },
  importFile(file: File) {
    const data = new FormData();
    data.append("file", file);
    return http.post<unknown, Job>("/jobs/import/file", data, { timeout: 120000 });
  },
  importImage(file: File) {
    const data = new FormData();
    data.append("file", file);
    return http.post<unknown, Job>("/jobs/import/image", data, { timeout: 120000 });
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
  },
  updateStatus(id: number, payload: { status: string; note?: string | null }) {
    return http.post<unknown, Application>(`/applications/${id}/status`, payload);
  },
  kanban() {
    return http.get<unknown, Record<string, Application[]>>("/applications/kanban");
  }
};

export const matchingApi = {
  calculate(payload: { resume_id: number; job_id: number }) {
    return http.post<unknown, MatchReport>("/matching/calculate", payload);
  },
  get(id: number) {
    return http.get<unknown, MatchReport>(`/matching/reports/${id}`);
  }
};

export const statisticsApi = {
  overview() {
    return http.get<unknown, StatisticsOverview>("/statistics/overview");
  },
  applications() {
    return http.get<unknown, StatisticsApplications>("/statistics/applications");
  },
  jobs() {
    return http.get<unknown, StatisticsJobs>("/statistics/jobs");
  },
  matches() {
    return http.get<unknown, StatisticsMatches>("/statistics/matches");
  }
};

export const reportApi = {
  list() {
    return http.get<unknown, Report[]>("/reports");
  },
  weekly() {
    return http.post<unknown, Report>("/ai/reports/weekly", undefined, { timeout: 120000 });
  },
  remove(id: number) {
    return http.delete<unknown, null>(`/reports/${id}`);
  }
};

export const aiApi = {
  generateResume(text: string) {
    return http.post<unknown, AIResult>("/ai/resumes/generate-from-text", { text });
  },
  parseResume(text: string) {
    return http.post<unknown, AIResult>("/ai/resumes/parse-file", { text });
  },
  parseResumeUpload(file: File) {
    const data = new FormData();
    data.append("file", file);
    return http.post<unknown, AIResult>("/ai/resumes/parse-upload", data, {
      timeout: 120000
    });
  },
  optimizeResume(text: string, resume_id?: number, job_id?: number) {
    return http.post<unknown, AIResult>("/ai/resumes/optimize", { text, resume_id, job_id }, { timeout: 120000 });
  },
  adaptResume(text: string, resume_id?: number, job_id?: number) {
    return http.post<unknown, AIResult>("/ai/resumes/adapt-to-job", { text, resume_id, job_id }, { timeout: 120000 });
  },
  interviewQuestions(text: string, resume_id?: number, job_id?: number) {
    return http.post<unknown, AIResult>("/ai/interviews/questions", { text, resume_id, job_id }, { timeout: 120000 });
  },
  evaluateAnswer(payload: { question: string; answer: string; resume_id?: number; job_id?: number }) {
    return http.post<unknown, AIResult>("/ai/interviews/evaluate-answer", payload, { timeout: 120000 });
  },
  chatResumeTemplate(payload: ResumeTemplateChatPayload) {
    return http.post<unknown, AIResult>("/ai/resume-templates/chat", payload, { timeout: 180000 });
  }
};

export const deliveryApi = {
  profile() {
    return http.get<unknown, DeliveryProfile>("/delivery/profiles/me");
  },
  updateProfile(payload: Partial<Pick<DeliveryProfile, "real_name" | "phone" | "email" | "school" | "major" | "common_answers">>) {
    return http.put<unknown, DeliveryProfile>("/delivery/profiles/me", payload);
  },
  createTask(payload: { job_id: number; resume_id?: number | null; site_name?: string | null; target_url?: string | null }) {
    return http.post<unknown, DeliveryTask>("/delivery/tasks", payload);
  },
  previewTask(id: number) {
    return http.post<unknown, { task: DeliveryTask; preview: Record<string, unknown> }>(`/delivery/tasks/${id}/preview`);
  },
  executeTask(id: number) {
    return http.post<unknown, DeliveryTask>(`/delivery/tasks/${id}/execute`);
  },
  logs(id: number) {
    return http.get<unknown, DeliveryTaskLog[]>(`/delivery/tasks/${id}/logs`);
  },
  getTask(id: number) {
    return http.get<unknown, DeliveryTask>(`/delivery/tasks/${id}`);
  },
  pollExecuteTask(taskId: number, workerTaskId: string) {
    return http.get<unknown, {
      task_status: string;
      task?: DeliveryTask;
      worker_task_id?: string;
    }>(`/delivery/tasks/${taskId}/execute/tasks/${workerTaskId}`);
  },
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
  },
  prompts() {
    return http.get<unknown, PromptTemplate[]>("/admin/prompts");
  },
  createPrompt(payload: Omit<PromptTemplate, "id" | "created_at" | "updated_at">) {
    return http.post<unknown, { id: number }>("/admin/prompts", payload);
  },
  deliverySites() {
    return http.get<unknown, DeliverySite[]>("/admin/delivery-sites");
  },
  updateDeliverySites(payload: DeliverySite[]) {
    return http.put<unknown, null>("/admin/delivery-sites", payload);
  }
};
