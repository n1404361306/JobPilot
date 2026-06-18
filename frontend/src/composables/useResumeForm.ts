import { computed, reactive, ref } from "vue";
import type { ResumeTemplateId } from "@/utils/resumeTemplates";
import { DEFAULT_RESUME_TEMPLATE_ID } from "@/utils/resumeTemplates";
import { snapshotFromPlainText } from "@/utils/resumeHelpers";

export type EditableEducation = {
  school: string;
  major: string;
  degree: string;
  period: string;
  research_direction: string;
  gpa: string;
  highlightsText: string;
};

export type EditableWork = {
  company: string;
  position: string;
  period: string;
  location: string;
  description: string;
  responsibilitiesText: string;
  techStackText: string;
};

export type EditableProject = {
  project_name: string;
  type: string;
  period: string;
  description: string;
  responsibilitiesText: string;
  techStackText: string;
  resultsText: string;
};

export type ResumeFormSnapshot = {
  basic_info: {
    name: string;
    phone: string;
    email: string;
    github: string;
    website: string;
    location: string;
    photo: string;
  };
  job_intention: string;
  summary: string;
  skillsText: {
    languages: string;
    backend: string;
    database: string;
    ai: string;
    tools: string;
    language_ability: string;
  };
  education: EditableEducation[];
  internships: EditableWork[];
  projects: EditableProject[];
  researchText: string;
  awardsText: string;
  certificatesText: string;
  open_source: string;
  interests: string;
  self_evaluation: string;
  missingText: string;
  templateId?: ResumeTemplateId;
};

export const RESUME_FORM_MARKER = "<!--RESUME_FORM";

function unpackContent(content: string) {
  const markerIndex = content.lastIndexOf(RESUME_FORM_MARKER);
  if (markerIndex === -1) {
    return { displayContent: content, snapshot: null as ResumeFormSnapshot | null };
  }

  const jsonStart = content.indexOf("\n", markerIndex) + 1;
  const jsonEnd = content.lastIndexOf("\n-->");
  if (jsonStart <= 0 || jsonEnd <= jsonStart) {
    return { displayContent: content.slice(0, markerIndex).trim(), snapshot: null };
  }

  try {
    const snapshot = JSON.parse(content.slice(jsonStart, jsonEnd)) as ResumeFormSnapshot;
    return { displayContent: content.slice(0, markerIndex).trim(), snapshot };
  } catch {
    return { displayContent: content.slice(0, markerIndex).trim(), snapshot: null };
  }
}

export function getResumeDisplayContent(content: string) {
  return unpackContent(content).displayContent;
}

export function getResumeSnapshot(content: string) {
  return unpackContent(content).snapshot;
}

export function getResumeTemplateId(content: string): ResumeTemplateId {
  return getResumeSnapshot(content)?.templateId ?? DEFAULT_RESUME_TEMPLATE_ID;
}

export function applyTemplateToResumeContent(content: string, templateId: ResumeTemplateId) {
  const { displayContent, snapshot } = unpackContent(content);
  const baseText = displayContent || content.trim();
  const nextSnapshot: ResumeFormSnapshot = snapshot
    ? { ...snapshot, templateId }
    : { ...snapshotFromPlainText(baseText), templateId };
  return `${baseText}\n\n${RESUME_FORM_MARKER}\n${JSON.stringify(nextSnapshot)}\n-->`;
}

function emptyEducation(): EditableEducation {
  return {
    school: "",
    major: "",
    degree: "",
    period: "",
    research_direction: "",
    gpa: "",
    highlightsText: ""
  };
}

function emptyWork(): EditableWork {
  return {
    company: "",
    position: "",
    period: "",
    location: "",
    description: "",
    responsibilitiesText: "",
    techStackText: ""
  };
}

function emptyProject(): EditableProject {
  return {
    project_name: "",
    type: "",
    period: "",
    description: "",
    responsibilitiesText: "",
    techStackText: "",
    resultsText: ""
  };
}

function arr(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String).filter(Boolean);
  if (typeof value === "string" && value.trim()) {
    return value.split(/[、,，；;\n]/).map((item) => item.trim()).filter(Boolean);
  }
  return [];
}

function join(value: unknown) {
  return arr(value).join("\n");
}

function toObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function sectionList(textValue: string): string {
  return textValue
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => `  ${item}`)
    .join("\n");
}

export function useResumeForm() {
  const resumeForm = reactive({
    basic_info: { name: "", phone: "", email: "", github: "", website: "", location: "", photo: "" },
    job_intention: "",
    summary: "",
    education: [] as EditableEducation[],
    internships: [] as EditableWork[],
    projects: [] as EditableProject[],
    open_source: "",
    interests: "",
    self_evaluation: ""
  });

  const skillsText = reactive({
    languages: "",
    backend: "",
    database: "",
    ai: "",
    tools: "",
    language_ability: ""
  });

  const researchText = ref("");
  const awardsText = ref("");
  const certificatesText = ref("");
  const missingText = ref("");

  function resetForm() {
    Object.assign(resumeForm.basic_info, {
      name: "",
      phone: "",
      email: "",
      github: "",
      website: "",
      location: "",
      photo: ""
    });
    resumeForm.job_intention = "";
    resumeForm.summary = "";
    resumeForm.education = [emptyEducation()];
    resumeForm.internships = [emptyWork()];
    resumeForm.projects = [emptyProject()];
    resumeForm.open_source = "";
    resumeForm.interests = "";
    resumeForm.self_evaluation = "";
    Object.assign(skillsText, {
      languages: "",
      backend: "",
      database: "",
      ai: "",
      tools: "",
      language_ability: ""
    });
    researchText.value = "";
    awardsText.value = "";
    certificatesText.value = "";
    missingText.value = "";
  }

  function fillForm(data: Record<string, unknown>) {
    const wrapped = toObject(data.resume_form);
    const source = Object.keys(wrapped).length > 0 ? wrapped : data;
    const basic = toObject(source.basic_info);
    Object.assign(resumeForm.basic_info, {
      name: String(basic.name || ""),
      phone: String(basic.phone || ""),
      email: String(basic.email || ""),
      github: String(basic.github || ""),
      website: String(basic.website || ""),
      location: String(basic.location || ""),
      photo: String(basic.photo || "")
    });
    resumeForm.job_intention = String(source.job_intention || "");
    resumeForm.summary = String(source.summary || "");

    const skills = toObject(source.skills);
    Object.assign(skillsText, {
      languages: join(skills.languages),
      backend: join(skills.backend),
      database: join(skills.database),
      ai: join(skills.ai),
      tools: join(skills.tools),
      language_ability: join(skills.language_ability)
    });

    resumeForm.education = Array.isArray(source.education) && source.education.length
      ? (source.education as Record<string, unknown>[]).map((item) => ({
          school: String(item.school || ""),
          major: String(item.major || ""),
          degree: String(item.degree || ""),
          period: String(item.period || ""),
          research_direction: String(item.research_direction || ""),
          gpa: String(item.gpa || ""),
          highlightsText: join(item.highlights)
        }))
      : [emptyEducation()];

    resumeForm.internships = Array.isArray(source.internships) && source.internships.length
      ? (source.internships as Record<string, unknown>[]).map((item) => ({
          company: String(item.company || ""),
          position: String(item.position || ""),
          period: String(item.period || ""),
          location: String(item.location || ""),
          description: String(item.description || ""),
          responsibilitiesText: join(item.responsibilities),
          techStackText: join(item.tech_stack)
        }))
      : [emptyWork()];

    resumeForm.projects = Array.isArray(source.projects) && source.projects.length
      ? (source.projects as Record<string, unknown>[]).map((item) => ({
          project_name: String(item.project_name || ""),
          type: String(item.type || ""),
          period: String(item.period || ""),
          description: String(item.description || ""),
          responsibilitiesText: join(item.responsibilities),
          techStackText: join(item.tech_stack),
          resultsText: join(item.results)
        }))
      : [emptyProject()];

    researchText.value = Array.isArray(source.research)
      ? (source.research as Record<string, unknown>[])
          .map((item) => [item.title, item.period, ...arr(item.content)].filter(Boolean).join("\n"))
          .join("\n\n")
      : "";
    awardsText.value = join(source.awards);
    certificatesText.value = join(source.certificates);
    resumeForm.open_source = String(source.open_source || "");
    resumeForm.interests = String(source.interests || "");
    resumeForm.self_evaluation = String(source.self_evaluation || "");
    missingText.value = join(source.missing_items);
  }

  function exportSnapshot(): ResumeFormSnapshot {
    return {
      basic_info: { ...resumeForm.basic_info },
      job_intention: resumeForm.job_intention,
      summary: resumeForm.summary,
      skillsText: { ...skillsText },
      education: resumeForm.education.map((item) => ({ ...item })),
      internships: resumeForm.internships.map((item) => ({ ...item })),
      projects: resumeForm.projects.map((item) => ({ ...item })),
      researchText: researchText.value,
      awardsText: awardsText.value,
      certificatesText: certificatesText.value,
      open_source: resumeForm.open_source,
      interests: resumeForm.interests,
      self_evaluation: resumeForm.self_evaluation,
      missingText: missingText.value
    };
  }

  function importSnapshot(snapshot: ResumeFormSnapshot) {
    Object.assign(resumeForm.basic_info, { photo: "" }, snapshot.basic_info);
    resumeForm.job_intention = snapshot.job_intention;
    resumeForm.summary = snapshot.summary;
    Object.assign(skillsText, snapshot.skillsText);
    resumeForm.education = snapshot.education.length ? snapshot.education.map((item) => ({ ...item })) : [emptyEducation()];
    resumeForm.internships = snapshot.internships.length ? snapshot.internships.map((item) => ({ ...item })) : [emptyWork()];
    resumeForm.projects = snapshot.projects.length ? snapshot.projects.map((item) => ({ ...item })) : [emptyProject()];
    researchText.value = snapshot.researchText;
    awardsText.value = snapshot.awardsText;
    certificatesText.value = snapshot.certificatesText;
    resumeForm.open_source = snapshot.open_source;
    resumeForm.interests = snapshot.interests;
    resumeForm.self_evaluation = snapshot.self_evaluation;
    missingText.value = snapshot.missingText;
  }

  const resumeContent = computed(() => {
    const lines = [
      "基本信息",
      `姓名：${resumeForm.basic_info.name}`,
      `电话：${resumeForm.basic_info.phone}`,
      `邮箱：${resumeForm.basic_info.email}`,
      `GitHub：${resumeForm.basic_info.github}`,
      `个人网站：${resumeForm.basic_info.website}`,
      `所在地：${resumeForm.basic_info.location}`,
      "",
      "求职意向",
      resumeForm.job_intention,
      "",
      "个人简介",
      resumeForm.summary,
      "",
      "专业技能",
      `编程语言：${skillsText.languages.replace(/\n/g, "、")}`,
      `后端开发：${skillsText.backend.replace(/\n/g, "、")}`,
      `数据库与中间件：${skillsText.database.replace(/\n/g, "、")}`,
      `AI / 算法：${skillsText.ai.replace(/\n/g, "、")}`,
      `工程工具：${skillsText.tools.replace(/\n/g, "、")}`,
      `语言能力：${skillsText.language_ability.replace(/\n/g, "、")}`,
      "",
      "教育经历",
      ...resumeForm.education.flatMap((item, index) => [
        `${index + 1}. ${item.school}｜${item.major}｜${item.degree}｜${item.period}`,
        `   研究方向：${item.research_direction}`,
        `   GPA：${item.gpa}`,
        `   课程/荣誉：${item.highlightsText.replace(/\n/g, "；")}`
      ]),
      "",
      "实习经历",
      ...resumeForm.internships.flatMap((item, index) => [
        `${index + 1}. ${item.company}｜${item.position}｜${item.period}｜${item.location}`,
        `   工作概述：${item.description}`,
        `   主要工作：\n${sectionList(item.responsibilitiesText)}`,
        `   技术栈：${item.techStackText.replace(/\n/g, "、")}`
      ]),
      "",
      "项目经历",
      ...resumeForm.projects.flatMap((item, index) => [
        `${index + 1}. ${item.project_name}｜${item.type}｜${item.period}`,
        `   项目概述：${item.description}`,
        `   主要职责：\n${sectionList(item.responsibilitiesText)}`,
        `   技术栈：${item.techStackText.replace(/\n/g, "、")}`,
        `   项目成果：\n${sectionList(item.resultsText)}`
      ]),
      "",
      "科研经历",
      researchText.value,
      "",
      "获奖证书",
      `获奖经历：\n${sectionList(awardsText.value)}`,
      `证书：${certificatesText.value.replace(/\n/g, "、")}`,
      `开源贡献：${resumeForm.open_source}`,
      `兴趣方向：${resumeForm.interests}`,
      `个人评价：${resumeForm.self_evaluation}`,
      "",
      "待补充内容",
      missingText.value || "暂无"
    ];
    return lines.join("\n").replace(/\n{3,}/g, "\n\n").trim();
  });

  function packStoredContent(templateId?: ResumeTemplateId) {
    const snapshot = exportSnapshot();
    if (templateId) {
      snapshot.templateId = templateId;
    }
    return `${resumeContent.value}\n\n${RESUME_FORM_MARKER}\n${JSON.stringify(snapshot)}\n-->`;
  }

  function unpackStoredContent(content: string) {
    return unpackContent(content);
  }

  function addEducation() {
    resumeForm.education.push(emptyEducation());
  }

  function removeEducation(index: number) {
    resumeForm.education.splice(index, 1);
    if (!resumeForm.education.length) {
      resumeForm.education.push(emptyEducation());
    }
  }

  function addInternship() {
    resumeForm.internships.push(emptyWork());
  }

  function removeInternship(index: number) {
    resumeForm.internships.splice(index, 1);
    if (!resumeForm.internships.length) {
      resumeForm.internships.push(emptyWork());
    }
  }

  function addProject() {
    resumeForm.projects.push(emptyProject());
  }

  function removeProject(index: number) {
    resumeForm.projects.splice(index, 1);
    if (!resumeForm.projects.length) {
      resumeForm.projects.push(emptyProject());
    }
  }

  return {
    resumeForm,
    skillsText,
    researchText,
    awardsText,
    certificatesText,
    missingText,
    resumeContent,
    resetForm,
    fillForm,
    exportSnapshot,
    importSnapshot,
    packStoredContent,
    unpackStoredContent,
    addEducation,
    removeEducation,
    addInternship,
    removeInternship,
    addProject,
    removeProject
  };
}
