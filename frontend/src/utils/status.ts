import type { ApplicationStatus, JobStatus } from "@/api/types";

export const applicationStatusLabels: Record<ApplicationStatus, string> = {
  pending: "待处理",
  submitted: "已投递",
  interview: "面试中",
  offer: "Offer",
  rejected: "已拒绝",
  withdrawn: "已撤回"
};

export const applicationStatusTypes: Record<ApplicationStatus, "info" | "success" | "warning" | "danger" | "primary"> = {
  pending: "info",
  submitted: "primary",
  interview: "warning",
  offer: "success",
  rejected: "danger",
  withdrawn: "info"
};

export const applicationStatusOrder: ApplicationStatus[] = [
  "pending",
  "submitted",
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
