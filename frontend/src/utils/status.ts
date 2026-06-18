import type { ApplicationStatus, JobStatus } from "@/api/types";

export const applicationStatusLabels: Record<ApplicationStatus, string> = {
  pending: "待投递",
  submitted: "已投递",
  screening: "筛选中",
  written: "笔试",
  tech_first: "技术一面",
  tech_second: "技术二面",
  hr_interview: "HR 面",
  interview: "面试中",
  offer: "Offer",
  rejected: "已拒绝",
  withdrawn: "已放弃"
};

export const applicationStatusTypes: Record<ApplicationStatus, "info" | "success" | "warning" | "danger" | "primary"> = {
  pending: "info",
  submitted: "primary",
  screening: "warning",
  written: "warning",
  tech_first: "warning",
  tech_second: "warning",
  hr_interview: "warning",
  interview: "warning",
  offer: "success",
  rejected: "danger",
  withdrawn: "info"
};

export const applicationStatusOrder: ApplicationStatus[] = [
  "pending",
  "submitted",
  "screening",
  "written",
  "tech_first",
  "tech_second",
  "hr_interview",
  "interview",
  "offer",
  "rejected",
  "withdrawn"
];

export const jobStatusLabels: Record<JobStatus, string> = {
  active: "招聘中",
  closed: "已关闭",
  archived: "已归档"
};

export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export function asApplicationStatus(value: string): ApplicationStatus {
  return applicationStatusOrder.includes(value as ApplicationStatus) ? (value as ApplicationStatus) : "pending";
}
