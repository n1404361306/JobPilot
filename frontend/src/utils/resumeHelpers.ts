import type { ResumeFormSnapshot } from "@/composables/useResumeForm";
import { isPhotoDataUrl } from "@/utils/photoUpload";

export function textLines(text: string) {
  return text
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function hasPhoto(snapshot: ResumeFormSnapshot) {
  return isPhotoDataUrl(snapshot.basic_info.photo);
}

export function hasText(value?: string | null) {
  return Boolean(value?.trim());
}

export function contactItems(snapshot: ResumeFormSnapshot) {
  const { basic_info } = snapshot;
  return [
    { label: "电话", value: basic_info.phone },
    { label: "邮箱", value: basic_info.email },
    { label: "GitHub", value: basic_info.github },
    { label: "网站", value: basic_info.website },
    { label: "所在地", value: basic_info.location }
  ].filter((item) => hasText(item.value));
}

export function skillGroups(snapshot: ResumeFormSnapshot) {
  const { skillsText } = snapshot;
  return [
    { label: "编程语言", value: skillsText.languages },
    { label: "后端开发", value: skillsText.backend },
    { label: "数据库与中间件", value: skillsText.database },
    { label: "AI / 算法", value: skillsText.ai },
    { label: "工程工具", value: skillsText.tools },
    { label: "语言能力", value: skillsText.language_ability }
  ].filter((item) => hasText(item.value));
}

export function hasEducation(snapshot: ResumeFormSnapshot) {
  return snapshot.education.some((item) => hasText(item.school) || hasText(item.major));
}

export function hasInternships(snapshot: ResumeFormSnapshot) {
  return snapshot.internships.some((item) => hasText(item.company) || hasText(item.position));
}

export function hasProjects(snapshot: ResumeFormSnapshot) {
  return snapshot.projects.some((item) => hasText(item.project_name) || hasText(item.description));
}

export function createSampleSnapshot(): ResumeFormSnapshot {
  return {
    basic_info: {
      name: "张明",
      phone: "138-0000-0000",
      email: "zhangming@example.com",
      github: "github.com/zhangming",
      website: "zhangming.dev",
      location: "上海",
      photo: ""
    },
    job_intention: "后端开发工程师 / Java 方向",
    summary: "计算机专业硕士，具备扎实的 Java 后端开发基础，熟悉 Spring Boot 微服务与 MySQL 调优，有互联网公司实习与开源项目经验。",
    skillsText: {
      languages: "Java\nPython\nGo",
      backend: "Spring Boot\nMyBatis\nRedis\nKafka",
      database: "MySQL\nPostgreSQL\nElasticsearch",
      ai: "PyTorch\nScikit-learn",
      tools: "Git\nDocker\nLinux\nMaven",
      language_ability: "CET-6\n英语读写熟练"
    },
    education: [
      {
        school: "华东师范大学",
        major: "计算机科学与技术",
        degree: "硕士",
        period: "2023.09 - 2026.06",
        research_direction: "分布式系统",
        gpa: "3.8 / 4.0",
        highlightsText: "国家奖学金\n优秀研究生"
      }
    ],
    internships: [
      {
        company: "某互联网科技",
        position: "后端开发实习生",
        period: "2025.06 - 2025.09",
        location: "上海",
        description: "参与订单中心服务重构，负责接口开发与性能优化。",
        responsibilitiesText: "设计并实现 RESTful API\n编写单元测试与接口文档\n协助排查线上慢 SQL",
        techStackText: "Java\nSpring Boot\nMySQL\nRedis"
      }
    ],
    projects: [
      {
        project_name: "JobPilot 求职助手",
        type: "全栈项目",
        period: "2025.10 - 2026.03",
        description: "面向高校学生的智能求职平台，支持简历生成、岗位匹配与投递管理。",
        responsibilitiesText: "负责后端 API 与数据库设计\n实现 AI 简历解析与匹配评分模块",
        techStackText: "FastAPI\nVue 3\nPostgreSQL",
        resultsText: "完成 20+ 业务接口\n匹配报告生成耗时降低 40%"
      }
    ],
    researchText: "",
    awardsText: "全国大学生数学建模竞赛 省一等奖",
    certificatesText: "软件设计师",
    open_source: "参与开源项目 X，提交 12 个 PR",
    interests: "技术博客、长跑",
    self_evaluation: "学习能力强，沟通协作顺畅，对代码质量有较高要求。",
    missingText: ""
  };
}

export function snapshotFromPlainText(content: string): ResumeFormSnapshot {
  return {
    basic_info: { name: "", phone: "", email: "", github: "", website: "", location: "", photo: "" },
    job_intention: "",
    summary: content,
    skillsText: { languages: "", backend: "", database: "", ai: "", tools: "", language_ability: "" },
    education: [],
    internships: [],
    projects: [],
    researchText: "",
    awardsText: "",
    certificatesText: "",
    open_source: "",
    interests: "",
    self_evaluation: "",
    missingText: ""
  };
}
