export interface ResumeTemplateFieldSpec {
  key: string;
  label: string;
  format: string;
  required: boolean;
}

export const RESUME_TEMPLATE_FIELD_SPECS: ResumeTemplateFieldSpec[] = [
  { key: "name", label: "姓名", format: "纯文本", required: true },
  { key: "phone", label: "电话", format: "纯文本", required: true },
  { key: "email", label: "邮箱", format: "纯文本", required: true },
  { key: "github", label: "GitHub", format: "纯文本", required: false },
  { key: "website", label: "个人网站", format: "纯文本", required: false },
  { key: "location", label: "所在地", format: "纯文本", required: false },
  { key: "photo", label: "照片", format: "<img src=\"{{photo}}\">", required: false },
  { key: "job_intention", label: "求职意向", format: "文本，支持换行", required: true },
  { key: "summary", label: "个人简介", format: "<p> 包裹", required: true },
  { key: "skills", label: "专业技能", format: "多个 <li>，须放在 <ul> 内", required: true },
  { key: "education", label: "教育经历", format: "HTML 区块，勿外包 <ul>", required: true },
  { key: "internships", label: "实习经历", format: "HTML 区块，勿外包 <ul>", required: true },
  { key: "projects", label: "项目经历", format: "HTML 区块，勿外包 <ul>", required: true },
  { key: "research", label: "科研经历", format: "<p> 包裹", required: true },
  { key: "awards", label: "荣誉奖项", format: "多个 <li>，须放在 <ul> 内", required: true },
  { key: "certificates", label: "证书资质", format: "<p> 包裹", required: true },
  { key: "open_source", label: "开源贡献", format: "<p> 包裹", required: true },
  { key: "interests", label: "兴趣爱好", format: "<p> 包裹", required: true },
  { key: "self_evaluation", label: "自我评价", format: "<p> 包裹", required: true },
  { key: "missing", label: "待补充", format: "<p> 包裹", required: true }
];

export const REQUIRED_TEMPLATE_FIELDS = RESUME_TEMPLATE_FIELD_SPECS.filter((item) => item.required).map(
  (item) => item.key
);
