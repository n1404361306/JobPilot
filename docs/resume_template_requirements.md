# 用户自定义简历模板要求

本文档说明 JobPilot 用户上传简历模板的格式、占位符、接口和可见性规则。

## 1. 模板格式

- 支持文件类型：`.html`、`.htm`、`.txt`
- 编码：UTF-8
- 建议大小：不超过 256KB
- 模板内容建议是一段完整或局部 HTML，也可以是纯文本
- 模板通过 `{{变量名}}` 占位符读取简历表单数据

禁止内容：

- `<script>`、`<iframe>`、`<object>`、`<embed>`
- `javascript:` 链接
- `onclick`、`onload`、`onerror` 等事件脚本
- 外部不可信脚本或会自动执行的代码

## 2. 常用占位符

基础信息：

| 占位符 | 含义 |
|---|---|
| `{{name}}` / `{{basic_info.name}}` | 姓名 |
| `{{phone}}` / `{{basic_info.phone}}` | 电话 |
| `{{email}}` / `{{basic_info.email}}` | 邮箱 |
| `{{github}}` / `{{basic_info.github}}` | GitHub |
| `{{website}}` / `{{basic_info.website}}` | 个人网站 |
| `{{location}}` / `{{basic_info.location}}` | 所在地 |
| `{{photo}}` / `{{basic_info.photo}}` | 上传头像的 data URL |

简历内容：

| 占位符 | 含义 |
|---|---|
| `{{job_intention}}` | 求职意向 |
| `{{summary}}` | 个人简介 |
| `{{skills}}` | 专业技能，输出为 `<li>` 列表项 |
| `{{education}}` | 教育经历，输出为 HTML 分段 |
| `{{internships}}` | 实习经历，输出为 HTML 分段 |
| `{{projects}}` | 项目经历，输出为 HTML 分段 |
| `{{research}}` | 科研经历 |
| `{{awards}}` | 获奖经历，输出为 `<li>` 列表项 |
| `{{certificates}}` | 证书 |
| `{{open_source}}` | 开源贡献 |
| `{{interests}}` | 兴趣方向 |
| `{{self_evaluation}}` | 个人评价 |
| `{{missing}}` | 待补充内容 |

## 3. 模板示例

```html
<style>
  .resume { font-family: "Microsoft YaHei", sans-serif; color: #1f2937; }
  .header { border-bottom: 3px solid #2563eb; padding-bottom: 12px; }
  .photo { width: 88px; height: 108px; object-fit: cover; float: right; }
  h1 { margin: 0; font-size: 28px; }
  h2 { margin-top: 22px; color: #2563eb; font-size: 16px; }
</style>

<div class="resume">
  <div class="header">
    <img class="photo" src="{{photo}}" alt="" />
    <h1>{{name}}</h1>
    <p>{{job_intention}}</p>
    <p>{{phone}} · {{email}} · {{location}}</p>
  </div>

  <h2>个人简介</h2>
  <p>{{summary}}</p>

  <h2>专业技能</h2>
  <ul>{{skills}}</ul>

  <h2>教育经历</h2>
  {{education}}

  <h2>项目经历</h2>
  {{projects}}
</div>
```

如果简历没有头像，`{{photo}}` 会输出空字符串。模板中可以保留 `<img src="{{photo}}">`，浏览器会自动显示为空图；也可以自行用 CSS 控制布局。

## 4. 上传接口

接口：

```http
POST /api/resume-templates/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

表单字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | File | 是 | `.html`、`.htm` 或 `.txt` 模板文件 |
| `name` | string | 否 | 模板名称，默认使用文件名 |
| `description` | string | 否 | 模板说明 |
| `is_public` | boolean | 否 | 是否公开给其他用户，默认 `false` |

返回：

```json
{
  "code": 0,
  "message": "template uploaded",
  "data": {
    "id": 12,
    "user_id": 3,
    "name": "单栏技术岗模板",
    "description": "适合技术类简历",
    "content": "<div>...</div>",
    "enabled": true,
    "is_system": false,
    "is_public": false,
    "copied_from_id": null
  }
}
```

## 5. 查询和选择接口

查询可用模板：

```http
GET /api/resume-templates
```

返回范围：

- 系统模板
- 当前用户自己的模板
- 其他用户公开的模板

查询单个模板：

```http
GET /api/resume-templates/{template_id}
```

应用模板到简历：

```http
POST /api/resumes/{resume_id}/template
Content-Type: application/json
```

请求体：

```json
{
  "template_id": "custom:12"
}
```

内置模板使用固定 ID：`classic`、`modern`、`sidebar`、`minimal`。

用户上传模板使用 `custom:<模板数字ID>`，例如 `custom:12`。

## 6. 公开与私有规则

- 用户上传模板默认是私有模板，仅上传者可见、可选择、可修改。
- 上传时勾选“公开给其他用户”后，其他登录用户可以在模板库和模板选择弹窗中看到并使用。
- 其他用户不能修改或删除你的模板。
- 管理员可以维护系统模板和后台模板状态。
- 复制公开模板后，新副本默认归当前用户所有，并默认为私有。

## 7. 设计建议

- 页面宽度建议按 A4 预览区域设计，主容器宽度控制在 `720px` 到 `820px`。
- 尽量使用内联 `<style>`，避免依赖外部 CSS 文件。
- 字号建议：姓名 24-32px，一级标题 15-18px，正文 12-14px。
- 使用 `{{education}}`、`{{projects}}` 等分段占位符时，系统会输出基础 HTML，可用 `.custom-item`、`.custom-item h3` 继续控制样式。
- 不建议使用复杂定位、动画或远程字体，导出 PDF 时可能导致排版不稳定。
