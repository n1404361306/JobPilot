# 用户自定义简历模板要求

本文档说明 JobPilot 用户上传简历模板的格式、占位符、接口和可见性规则。

## 模板格式

- 支持 `.html`、`.htm`、`.txt`
- 使用 UTF-8 编码
- 建议小于 256KB
- 使用 `{{变量名}}` 插入简历表单数据
- 禁止 `<script>`、`<iframe>`、`javascript:` 和 `onclick/onload/onerror` 等脚本内容

## 常用占位符

基础信息：`{{name}}`、`{{phone}}`、`{{email}}`、`{{github}}`、`{{website}}`、`{{location}}`、`{{photo}}`

简历内容：`{{job_intention}}`、`{{summary}}`、`{{skills}}`、`{{education}}`、`{{internships}}`、`{{projects}}`、`{{research}}`、`{{awards}}`、`{{certificates}}`、`{{open_source}}`、`{{interests}}`、`{{self_evaluation}}`、`{{missing}}`

也支持 `{{basic_info.name}}`、`{{basic_info.email}}`、`{{basic_info.photo}}` 这类基础信息路径写法。

## 示例

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

## 上传接口

`POST /api/resume-templates/upload`

`multipart/form-data` 字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `file` | File | 模板文件 |
| `name` | string | 模板名称 |
| `description` | string | 模板描述 |
| `is_public` | boolean | 是否公开，默认 `false` |

## 选择接口

`POST /api/resumes/{resume_id}/template`

```json
{
  "template_id": "custom:12"
}
```

内置模板 ID：`classic`、`modern`、`sidebar`、`minimal`。

用户模板 ID：`custom:<模板ID>`。

## 公开与私有

- 用户上传模板默认私有，仅自己可见和使用。
- 勾选公开后，其他登录用户可以查看和使用，但不能修改你的模板。
- 复制公开模板后，新副本归当前用户所有，并默认私有。
