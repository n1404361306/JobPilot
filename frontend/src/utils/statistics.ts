import type { Application, ApplicationStatus, Job, Resume } from "@/api/types";
import { applicationStatusOrder, asApplicationStatus } from "./status";

export type ApplicationSummary = Record<ApplicationStatus, number>;

export interface DashboardMetrics {
  resumeCount: number;
  defaultResumeCount: number;
  activeJobCount: number;
  applicationCount: number;
  interviewCount: number;
  offerCount: number;
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

export function buildDashboardMetrics(resumes: Resume[], jobs: Job[], applications: Application[]): DashboardMetrics {
  const summary = buildApplicationSummary(applications);

  return {
    resumeCount: resumes.length,
    defaultResumeCount: resumes.filter((resume) => resume.is_default).length,
    activeJobCount: jobs.filter((job) => job.status === "active").length,
    applicationCount: applications.length,
    interviewCount: summary.interview,
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
