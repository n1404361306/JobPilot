import type { ResumeTemplate } from "@/api/types";

export type BuiltInResumeTemplateId = "classic" | "modern" | "sidebar" | "minimal";
export type CustomResumeTemplateId = `custom:${number}`;
export type ResumeTemplateId = BuiltInResumeTemplateId | CustomResumeTemplateId;

export interface ResumeTemplatePreset {  id: BuiltInResumeTemplateId;
  name: string;
  description: string;
  accent: string;
  accentLight: string;
  accentDark: string;
}

export const RESUME_TEMPLATE_PRESETS: ResumeTemplatePreset[] = [
  {
    id: "classic",
    name: "经典商务",
    description: "居中标题、清晰分区，适合通用校招与社招场景。",
    accent: "#1e3a5f",
    accentLight: "#3d628f",
    accentDark: "#142840"
  },
  {
    id: "modern",
    name: "现代蓝调",
    description: "顶部色块强调个人信息，层次分明、阅读节奏快。",
    accent: "#2563eb",
    accentLight: "#4f83f7",
    accentDark: "#1d4ed8"
  },
  {
    id: "sidebar",
    name: "侧边栏",
    description: "左侧展示联系方式与技能，右侧突出项目与实习经历。",
    accent: "#0f766e",
    accentLight: "#14b8a6",
    accentDark: "#0d5f59"
  },
  {
    id: "minimal",
    name: "极简留白",
    description: "大留白与细线分隔，适合设计、产品等偏审美岗位。",
    accent: "#374151",
    accentLight: "#6b7280",
    accentDark: "#111827"
  }
];

export const DEFAULT_RESUME_TEMPLATE_ID: ResumeTemplateId = "classic";

export function getTemplatePreset(id: ResumeTemplateId) {
  return RESUME_TEMPLATE_PRESETS.find((item) => item.id === id) ?? RESUME_TEMPLATE_PRESETS[0];
}

export function isCustomTemplateId(id: ResumeTemplateId | string): id is CustomResumeTemplateId {
  return /^custom:\d+$/.test(id);
}

export function customTemplateId(id: number): CustomResumeTemplateId {
  return `custom:${id}`;
}

export function parseCustomTemplateId(id: ResumeTemplateId | string) {
  return isCustomTemplateId(id) ? Number(id.split(":")[1]) : null;
}

export function parseResumeTemplateQuery(value: unknown): ResumeTemplateId | null {
  if (typeof value !== "string" || !value.trim()) {
    return null;
  }
  const normalized = value.trim();
  if (isCustomTemplateId(normalized)) {
    return normalized;
  }
  if (RESUME_TEMPLATE_PRESETS.some((item) => item.id === normalized)) {
    return normalized as ResumeTemplateId;
  }
  return null;
}

export function filterSelectableCustomTemplates(templates: ResumeTemplate[]) {
  return templates.filter((template) => template.user_id != null);
}

export function findCustomTemplateContent(templates: ResumeTemplate[], templateId: ResumeTemplateId | string) {
  const id = parseCustomTemplateId(templateId);
  if (!id) return "";
  return templates.find((template) => template.id === id)?.content ?? "";
}

export function getCustomTemplateLabel(templates: ResumeTemplate[], templateId: ResumeTemplateId | string) {
  const id = parseCustomTemplateId(templateId);
  if (!id) return getTemplatePreset(templateId as ResumeTemplateId).name;
  return templates.find((template) => template.id === id)?.name ?? "用户模板";
}
