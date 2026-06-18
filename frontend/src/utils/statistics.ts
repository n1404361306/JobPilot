import type { Application, ApplicationStatus, Job, Resume } from "@/api/types";
import { applicationStatusOrder, asApplicationStatus } from "./status";

export type ApplicationSummary = Record<ApplicationStatus, number>;

export const INTERVIEW_PIPELINE_STATUSES: ApplicationStatus[] = [
  "written",
  "tech_first",
  "tech_second",
  "hr_interview",
  "interview",
  "offer"
];

export const MATCH_SCORE_RANGE_ORDER = ["0-59", "60-79", "80-100"] as const;

export const jobSourceLabels: Record<string, string> = {
  manual: "手动录入",
  text: "文本导入",
  url: "链接导入",
  file: "文件导入",
  image: "截图导入",
  batch_text: "批量导入"
};

export interface DashboardMetrics {
  resumeCount: number;
  defaultResumeCount: number;
  activeJobCount: number;
  applicationCount: number;
  interviewCount: number;
  offerCount: number;
}

export function normalizeStatusCounts(counts: Record<string, number> | null | undefined): Record<string, number> {
  const normalized: Record<string, number> = {};
  for (const [status, count] of Object.entries(counts || {})) {
    const key = asApplicationStatus(status);
    normalized[key] = (normalized[key] || 0) + count;
  }
  return normalized;
}

export function formatPercentRate(rate: number | null | undefined, digits = 1): string {
  const value = Number(rate ?? 0);
  const percent = value <= 1 ? value * 100 : value;
  return `${percent.toFixed(digits)}%`;
}

export function buildApplicationSummary(applications: Application[]): ApplicationSummary {
  const summary = applicationStatusOrder.reduce((acc, status) => {
    acc[status] = 0;
    return acc;
  }, {} as ApplicationSummary);

  for (const application of applications) {
    summary[asApplicationStatus(application.status)] += 1;
  }

  return summary;
}

export function countInterviewPipeline(summary: ApplicationSummary): number {
  return INTERVIEW_PIPELINE_STATUSES.reduce((total, status) => total + summary[status], 0);
}

export function buildDashboardMetrics(resumes: Resume[], jobs: Job[], applications: Application[]): DashboardMetrics {
  const summary = buildApplicationSummary(applications);

  return {
    resumeCount: resumes.length,
    defaultResumeCount: resumes.filter((resume) => resume.is_default).length,
    activeJobCount: jobs.filter((job) => job.status === "active").length,
    applicationCount: applications.length,
    interviewCount: countInterviewPipeline(summary),
    offerCount: summary.offer
  };
}

export function buildChannelSummary(applications: Application[]) {
  const counts = new Map<string, number>();

  for (const application of applications) {
    const channel = application.channel || "未记录";
    counts.set(channel, (counts.get(channel) || 0) + 1);
  }

  return Array.from(counts.entries()).map(([name, value]) => ({ name, value }));
}

export function labelJobSource(source: string) {
  return jobSourceLabels[source] || source;
}

export function sortEntriesByCount(entries: Record<string, number>) {
  return Object.entries(entries).sort((left, right) => right[1] - left[1]);
}
