import { describe, expect, it } from "vitest";
import { buildApplicationSummary, buildDashboardMetrics } from "@/utils/statistics";
import type { Application, Job, Resume } from "@/api/types";

const resumes: Resume[] = [
  { id: 1, user_id: 1, title: "A", content: "x", file_url: null, is_default: true, created_at: "", updated_at: "" },
  { id: 2, user_id: 1, title: "B", content: "x", file_url: null, is_default: false, created_at: "", updated_at: "" }
];

const jobs: Job[] = [
  {
    id: 1,
    user_id: 1,
    title: "FE",
    company: "Acme",
    location: null,
    salary_range: null,
    source_url: null,
    source_type: null,
    job_type: null,
    deadline: null,
    tags: null,
    is_favorite: false,
    import_batch_id: null,
    description: null,
    status: "active",
    created_at: "",
    updated_at: ""
  },
  {
    id: 2,
    user_id: 1,
    title: "BE",
    company: "Beta",
    location: null,
    salary_range: null,
    source_url: null,
    source_type: null,
    job_type: null,
    deadline: null,
    tags: null,
    is_favorite: false,
    import_batch_id: null,
    description: null,
    status: "closed",
    created_at: "",
    updated_at: ""
  }
];

const applications: Application[] = [
  { id: 1, user_id: 1, job_id: 1, resume_id: 1, status: "pending", channel: "BOSS", note: null, applied_at: null, created_at: "", updated_at: "" },
  { id: 2, user_id: 1, job_id: 2, resume_id: 1, status: "submitted", channel: "LinkedIn", note: null, applied_at: "", created_at: "", updated_at: "" },
  { id: 3, user_id: 1, job_id: 2, resume_id: null, status: "interview", channel: null, note: null, applied_at: "", created_at: "", updated_at: "" }
];

describe("statistics utilities", () => {
  it("groups applications by known statuses", () => {
    const summary = buildApplicationSummary(applications);

    expect(summary.pending).toBe(1);
    expect(summary.submitted).toBe(1);
    expect(summary.interview).toBe(1);
    expect(summary.offer).toBe(0);
  });

  it("builds dashboard metrics from real resource arrays", () => {
    const metrics = buildDashboardMetrics(resumes, jobs, applications);

    expect(metrics).toEqual({
      resumeCount: 2,
      defaultResumeCount: 1,
      activeJobCount: 1,
      applicationCount: 3,
      interviewCount: 1,
      offerCount: 0
    });
  });
});
