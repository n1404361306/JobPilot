export type ResumeTemplateId = "classic" | "modern" | "sidebar" | "minimal";

export interface ResumeTemplatePreset {
  id: ResumeTemplateId;
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
