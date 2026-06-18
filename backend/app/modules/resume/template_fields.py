"""Resume custom template placeholder specification for AI generation and validation."""

import re

# All placeholders the frontend renderer supports (see ResumeStyledPreview.renderCustomTemplate)
RESUME_TEMPLATE_PLACEHOLDERS: dict[str, str] = {
    "name": "姓名（纯文本）",
    "phone": "电话（纯文本）",
    "email": "邮箱（纯文本）",
    "github": "GitHub（纯文本）",
    "website": "个人网站（纯文本）",
    "location": "所在地（纯文本）",
    "photo": "照片 URL，用于 <img src=\"{{photo}}\">",
    "job_intention": "求职意向（可含换行，已转 <br>）",
    "summary": "个人简介（可含换行）",
    "skills": "技能列表项，渲染为多个 <li>，外层须包 <ul>",
    "education": "教育经历 HTML 区块（系统生成 .custom-item，勿再包 <ul>）",
    "internships": "实习经历 HTML 区块（系统生成 .custom-item）",
    "projects": "项目经历 HTML 区块（系统生成 .custom-item）",
    "research": "科研经历（可含换行）",
    "awards": "荣誉奖项，渲染为多个 <li>，外层须包 <ul>",
    "certificates": "证书资质（可含换行）",
    "open_source": "开源贡献（可含换行）",
    "interests": "兴趣爱好（可含换行）",
    "self_evaluation": "自我评价（可含换行）",
    "missing": "待补充内容（可含换行）",
}

REQUIRED_PLACEHOLDERS: tuple[str, ...] = (
    "name",
    "phone",
    "email",
    "job_intention",
    "summary",
    "skills",
    "education",
    "internships",
    "projects",
    "research",
    "awards",
    "certificates",
    "open_source",
    "interests",
    "self_evaluation",
    "missing",
)

RECOMMENDED_PLACEHOLDERS: tuple[str, ...] = ("photo", "github", "website", "location")

BASIC_INFO_ALIASES: dict[str, str] = {
    "basic_info.name": "name",
    "basic_info.phone": "phone",
    "basic_info.email": "email",
    "basic_info.github": "github",
    "basic_info.website": "website",
    "basic_info.location": "location",
    "basic_info.photo": "photo",
}

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def extract_template_placeholders(content: str) -> set[str]:
    found: set[str] = set()
    for match in _PLACEHOLDER_PATTERN.findall(content):
        key = match.strip()
        if key in BASIC_INFO_ALIASES:
            found.add(BASIC_INFO_ALIASES[key])
        elif key in RESUME_TEMPLATE_PLACEHOLDERS:
            found.add(key)
    return found


def find_missing_required_placeholders(content: str) -> list[str]:
    found = extract_template_placeholders(content)
    return [key for key in REQUIRED_PLACEHOLDERS if key not in found]


def build_ai_template_field_guide() -> str:
    lines = [
        "【必须包含的占位符与排版要求】",
        "模板必须覆盖以下全部字段（不可遗漏），每个字段都要有独立区块标题（如 h2）和合适容器：",
        "",
    ]
    for key in REQUIRED_PLACEHOLDERS:
        lines.append(f"- {{{{{key}}}}}：{RESUME_TEMPLATE_PLACEHOLDERS[key]}")
    lines.extend(
        [
            "",
            "【建议额外包含】",
            "- {{photo}}、{{github}}、{{website}}、{{location}}（页眉/联系方式区）",
            "",
            "【HTML 结构规范】",
            "1. 必须包含 <style>，至少定义：.resume-section、.resume-section h2、.custom-item、.custom-item h3、ul/li",
            "2. {{skills}}、{{awards}} 必须放在 <ul>...</ul> 内，因为系统输出的是 <li> 片段",
            "3. {{education}}、{{internships}}、{{projects}} 直接放入 section，不要外包 <ul>；系统会输出 <section class=\"custom-item\">...</section>",
            "4. {{summary}}、{{research}} 等文本字段用 <p> 或 <div> 包裹",
            "5. 页眉建议包含：{{photo}}、{{name}}、{{job_intention}}、{{phone}}、{{email}}、{{location}}",
            "6. 禁止使用 Jinja 语法（{% if %}、{% for %} 等）",
            "",
            "【推荐区块顺序】",
            "页眉 → 个人简介 → 专业技能 → 教育经历 → 实习经历 → 项目经历 → 科研经历 → 荣誉奖项 → 证书资质 → 开源贡献 → 兴趣爱好 → 自我评价 → 待补充",
        ]
    )
    return "\n".join(lines)


RESUME_TEMPLATE_AI_SYSTEM_PROMPT = (
    "你是 JobPilot 简历 HTML 模板设计专家。根据用户需求生成或修改简历展示模板。\n"
    "输出必须是合法 JSON，且只包含两个字段：\n"
    "- summary: 用中文简洁说明你做了哪些设计和修改（2-5 句，不使用 markdown）\n"
    "- template_content: 完整 HTML 模板字符串（必须含 <style>），使用 UTF-8\n\n"
    + build_ai_template_field_guide()
    + "\n\n"
    "【设计与修改原则】\n"
    "1. 首次生成必须包含上述全部必须字段，每个字段都要有清晰标题和排版，不可只写部分字段\n"
    "2. 用户要求修改时，在保留已有字段的前提下调整样式；不得删除必须字段\n"
    "3. 设计美观、专业，适合求职场景\n"
    "4. 禁止：<script> <iframe> <object> <embed> javascript: 及 onerror/onclick/onload 等事件（不要使用事件属性，照片仅用 <img src=\"{{photo}}\">）\n"
    "5. template_content 不要包裹 markdown 代码块"
)
