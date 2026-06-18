<template>
  <article
    ref="rootRef"
    class="resume-doc"
    :class="[`resume-doc--${templateClass}`, { 'resume-doc--compact': compact }]"
    :style="accentStyle"
  >
    <div v-if="isCustomTemplate && customHtml" class="custom-template" v-html="customHtml" />
    <template v-if="templateId === 'sidebar'">
      <div class="doc-layout">
        <aside class="doc-sidebar">
          <img v-if="hasPhoto" :src="photo" class="doc-photo doc-photo--sidebar" alt="个人照片" />
          <h1 class="doc-name">{{ displayName }}</h1>
          <p v-if="hasText(snapshot.job_intention)" class="doc-intention">{{ snapshot.job_intention }}</p>

          <section v-if="contactItemsList.length" class="doc-block">
            <h2 class="doc-block-title">联系方式</h2>
            <ul class="doc-list">
              <li v-for="item in contactItemsList" :key="item.label">
                <span class="doc-label">{{ item.label }}</span>
                <span>{{ item.value }}</span>
              </li>
            </ul>
          </section>

          <section v-if="skillGroupsList.length" class="doc-block">
            <h2 class="doc-block-title">专业技能</h2>
            <div v-for="item in skillGroupsList" :key="item.label" class="doc-skill">
              <strong>{{ item.label }}</strong>
              <p>{{ item.value.replace(/\n/g, " · ") }}</p>
            </div>
          </section>

          <section v-if="hasText(snapshot.awardsText) || hasText(snapshot.certificatesText)" class="doc-block">
            <h2 class="doc-block-title">荣誉证书</h2>
            <p v-if="hasText(snapshot.awardsText)" class="doc-text">{{ snapshot.awardsText }}</p>
            <p v-if="hasText(snapshot.certificatesText)" class="doc-text">{{ snapshot.certificatesText }}</p>
          </section>
        </aside>

        <main class="doc-main">
          <ResumeStyledSections :snapshot="snapshot" :show-skills="false" />
        </main>
      </div>
    </template>

    <template v-else-if="!isCustomTemplate">
      <header class="doc-header" :class="{ 'doc-header--banner': templateId === 'modern', 'doc-header--with-photo': hasPhoto }">
        <img v-if="hasPhoto" :src="photo" class="doc-photo" :class="`doc-photo--${templateId}`" alt="个人照片" />
        <div class="doc-header-content">
          <h1 class="doc-name">{{ displayName }}</h1>
          <p v-if="hasText(snapshot.job_intention)" class="doc-intention">{{ snapshot.job_intention }}</p>
          <div v-if="contactItemsList.length" class="doc-contact">
            <span v-for="item in contactItemsList" :key="item.label">{{ item.label }}：{{ item.value }}</span>
          </div>
        </div>
      </header>

      <div class="doc-body">
        <ResumeStyledSections
          :snapshot="snapshot"
          :show-skills="templateId !== 'minimal'"
          :variant="templateId === 'minimal' ? 'minimal' : 'default'"
        />
      </div>
    </template>
  </article>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { ResumeFormSnapshot } from "@/composables/useResumeForm";
import ResumeStyledSections from "@/components/ResumeStyledSections.vue";
import { contactItems, hasPhoto as snapshotHasPhoto, hasText, skillGroups } from "@/utils/resumeHelpers";
import { getTemplatePreset, isCustomTemplateId, type ResumeTemplateId } from "@/utils/resumeTemplates";

const props = withDefaults(
  defineProps<{
    snapshot: ResumeFormSnapshot;
    templateId?: ResumeTemplateId;
    customTemplateContent?: string;
    compact?: boolean;
  }>(),
  {
    templateId: "classic",
    compact: false
  }
);

const rootRef = ref<HTMLElement>();
const preset = computed(() => getTemplatePreset(props.templateId));
const isCustomTemplate = computed(() => isCustomTemplateId(props.templateId));
const templateClass = computed(() => (isCustomTemplate.value ? "custom" : props.templateId));
const accentStyle = computed(() => ({
  "--accent": preset.value.accent,
  "--accent-light": preset.value.accentLight,
  "--accent-dark": preset.value.accentDark,
  "--accent-soft": `${preset.value.accent}33`
}));
const displayName = computed(() => props.snapshot.basic_info.name || "未命名简历");
const photo = computed(() => props.snapshot.basic_info.photo || "");
const hasPhoto = computed(() => snapshotHasPhoto(props.snapshot));
const contactItemsList = computed(() => contactItems(props.snapshot));
const skillGroupsList = computed(() => skillGroups(props.snapshot));
const customHtml = computed(() => renderCustomTemplate(props.customTemplateContent || "", props.snapshot));

function escapeHtml(value: unknown) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function textBlock(value: unknown) {
  return escapeHtml(value).replace(/\n/g, "<br>");
}

function listBlock(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
}

function sectionItems(items: unknown[], fields: string[]) {
  return items
    .map((rawItem) => {
      const item = rawItem as Record<string, string>;
      const title = fields.map((field) => item[field]).filter(Boolean).join("｜");
      const detail = Object.entries(item)
        .filter(([key, value]) => !fields.includes(key) && hasText(value))
        .map(([, value]) => `<p>${textBlock(value)}</p>`)
        .join("");
      return `<section class="custom-item"><h3>${escapeHtml(title)}</h3>${detail}</section>`;
    })
    .join("");
}

function sanitizeTemplate(html: string) {
  const cleaned = html
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "")
    .replace(/<iframe[\s\S]*?>[\s\S]*?<\/iframe>/gi, "")
    .replace(/<object[\s\S]*?>[\s\S]*?<\/object>/gi, "")
    .replace(/<embed[\s\S]*?>/gi, "")
    .replace(/\son\w+="[^"]*"/gi, "")
    .replace(/\son\w+='[^']*'/gi, "")
    .replace(/javascript:/gi, "");
  return cleaned.replace(/<style\b[^>]*>([\s\S]*?)<\/style>/gi, (_match, css: string) => {
    return `<style>${scopeCssToTemplate(css)}</style>`;
  });
}

function splitSelectorList(selectorText: string) {
  const selectors: string[] = [];
  let current = "";
  let depth = 0;
  for (const char of selectorText) {
    if (char === "(" || char === "[") depth += 1;
    if (char === ")" || char === "]") depth = Math.max(0, depth - 1);
    if (char === "," && depth === 0) {
      selectors.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  if (current.trim()) selectors.push(current.trim());
  return selectors;
}

function scopeSelector(selector: string) {
  const trimmed = selector.trim();
  if (!trimmed || trimmed.startsWith(".custom-template")) return trimmed;
  if (/^(html|body|:root)([\s.#:[>+~]|$)/i.test(trimmed)) {
    return trimmed.replace(/^(html|body|:root)/i, ".custom-template");
  }
  return `.custom-template ${trimmed}`;
}

function scopeCssToTemplate(css: string) {
  const source = css.replace(/@import[^;]+;/gi, "").replace(/@page\s*{[\s\S]*?}/gi, "");
  let output = "";
  let index = 0;
  while (index < source.length) {
    const openIndex = source.indexOf("{", index);
    if (openIndex === -1) {
      output += source.slice(index);
      break;
    }

    const selectorText = source.slice(index, openIndex).trim();
    let depth = 1;
    let closeIndex = openIndex + 1;
    while (closeIndex < source.length && depth > 0) {
      const char = source[closeIndex];
      if (char === "{") depth += 1;
      if (char === "}") depth -= 1;
      closeIndex += 1;
    }

    const block = source.slice(openIndex + 1, closeIndex - 1);
    const lowerSelector = selectorText.toLowerCase();
    if (lowerSelector.startsWith("@media") || lowerSelector.startsWith("@supports") || lowerSelector.startsWith("@container")) {
      output += `${selectorText}{${scopeCssToTemplate(block)}}`;
    } else if (lowerSelector.startsWith("@keyframes") || lowerSelector.startsWith("@font-face")) {
      output += `${selectorText}{${block}}`;
    } else if (selectorText.startsWith("@")) {
      output += "";
    } else {
      const scopedSelector = splitSelectorList(selectorText).map(scopeSelector).filter(Boolean).join(", ");
      if (scopedSelector) {
        output += `${scopedSelector}{${block}}`;
      }
    }

    index = closeIndex;
  }
  return output;
}

function renderCustomTemplate(template: string, snapshot: ResumeFormSnapshot) {
  if (!template.trim()) return "";
  const values: Record<string, string> = {
    name: escapeHtml(snapshot.basic_info.name || "未命名简历"),
    phone: escapeHtml(snapshot.basic_info.phone),
    email: escapeHtml(snapshot.basic_info.email),
    github: escapeHtml(snapshot.basic_info.github),
    website: escapeHtml(snapshot.basic_info.website),
    location: escapeHtml(snapshot.basic_info.location),
    photo: snapshot.basic_info.photo ? escapeHtml(snapshot.basic_info.photo) : "",
    job_intention: textBlock(snapshot.job_intention),
    summary: textBlock(snapshot.summary),
    skills: listBlock(Object.values(snapshot.skillsText).filter(Boolean).join("\n")),
    education: sectionItems(snapshot.education, ["school", "major", "degree", "period"]),
    internships: sectionItems(snapshot.internships, ["company", "position", "period", "location"]),
    projects: sectionItems(snapshot.projects, ["project_name", "type", "period"]),
    research: textBlock(snapshot.researchText),
    awards: listBlock(snapshot.awardsText),
    certificates: textBlock(snapshot.certificatesText),
    open_source: textBlock(snapshot.open_source),
    interests: textBlock(snapshot.interests),
    self_evaluation: textBlock(snapshot.self_evaluation),
    missing: textBlock(snapshot.missingText)
  };
  const rendered = template.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (_match, key: string) => {
    if (key.startsWith("basic_info.")) {
      const field = key.split(".")[1] as keyof ResumeFormSnapshot["basic_info"];
      return escapeHtml(snapshot.basic_info[field]);
    }
    return values[key] ?? "";
  });
  return sanitizeTemplate(rendered);
}

defineExpose({
  getElement: () => rootRef.value
});
</script>

<style scoped>
.resume-doc {
  --accent: #1e3a5f;
  width: 100%;
  min-height: 780px;
  padding: 36px 40px;
  color: #1f2937;
  background: #fff;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.65;
  box-sizing: border-box;
}

.resume-doc--compact {
  min-height: auto;
  padding: 28px 32px;
}

.doc-name {
  margin: 0;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.doc-intention {
  margin: 8px 0 0;
  font-size: 15px;
  color: #4b5563;
}

.doc-contact {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 14px;
  font-size: 13px;
  color: #6b7280;
}

.doc-header {
  margin-bottom: 22px;
}

.doc-header--with-photo {
  display: flex;
  align-items: center;
  gap: 20px;
}

.doc-header--with-photo.doc-header--banner {
  justify-content: space-between;
  flex-direction: row-reverse;
}

.doc-header-content {
  flex: 1;
  min-width: 0;
}

.doc-photo {
  object-fit: cover;
  background: #fff;
  flex-shrink: 0;
}

.doc-photo--classic {
  width: 96px;
  height: 120px;
  border-radius: 8px;
  border: 3px solid var(--accent);
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.12);
}

.doc-photo--modern {
  width: 88px;
  height: 108px;
  border-radius: 10px;
  border: 2px solid rgba(255, 255, 255, 0.85);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18);
}

.doc-photo--sidebar {
  display: block;
  width: 108px;
  height: 132px;
  margin: 0 auto 16px;
  border-radius: 12px;
  border: 3px solid rgba(255, 255, 255, 0.85);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}

.doc-photo--minimal {
  width: 72px;
  height: 90px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}

.doc-header--banner {
  margin: -36px -40px 24px;
  padding: 28px 40px 22px;
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--accent-light));
}

.doc-header--banner .doc-intention,
.doc-header--banner .doc-contact {
  color: rgba(255, 255, 255, 0.92);
}

.doc-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 28px;
  min-height: 700px;
}

.doc-sidebar {
  padding: 22px 18px;
  border-radius: 10px;
  color: #f8fafc;
  background: linear-gradient(180deg, var(--accent), var(--accent-dark));
}

.doc-sidebar .doc-name {
  font-size: 24px;
  color: #fff;
}

.doc-sidebar .doc-intention {
  color: rgba(255, 255, 255, 0.88);
}

.doc-block {
  margin-top: 22px;
}

.doc-block-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.78);
}

.doc-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.doc-list li {
  margin-bottom: 8px;
  font-size: 12px;
  line-height: 1.5;
}

.doc-label {
  display: block;
  font-size: 11px;
  opacity: 0.72;
}

.doc-skill {
  margin-bottom: 10px;
  font-size: 12px;
}

.doc-skill strong {
  display: block;
  margin-bottom: 2px;
}

.doc-skill p {
  margin: 0;
  opacity: 0.92;
}

.doc-text {
  margin: 0 0 8px;
  font-size: 12px;
  white-space: pre-wrap;
}

.doc-main,
.doc-body {
  min-width: 0;
}

.custom-template {
  min-height: 700px;
}

.custom-template :deep(img) {
  max-width: 100%;
}

.custom-template :deep(.custom-item) {
  margin-bottom: 12px;
}

.custom-template :deep(.custom-item h3) {
  margin: 0 0 4px;
  font-size: 15px;
}

.custom-template :deep(ul) {
  margin: 0;
  padding-left: 20px;
}

.custom-template :deep(li) {
  margin-bottom: 4px;
}

.custom-template :deep(h2) {
  margin: 18px 0 8px;
  font-size: 16px;
}

.custom-template :deep(p) {
  margin: 0 0 8px;
}

.resume-doc--classic .doc-header {
  text-align: center;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--accent);
}

.resume-doc--classic .doc-header--with-photo {
  flex-direction: column;
}

.resume-doc--classic .doc-contact {
  justify-content: center;
}

.resume-doc--minimal {
  padding: 48px 52px;
}

.resume-doc--minimal .doc-name {
  font-size: 34px;
  font-weight: 500;
  letter-spacing: 0.06em;
}

.resume-doc--minimal .doc-header--with-photo {
  align-items: flex-start;
}

.resume-doc--minimal .doc-contact {
  margin-top: 18px;
  font-size: 12px;
  letter-spacing: 0.04em;
}

@media (max-width: 760px) {
  .resume-doc {
    padding: 24px;
    min-height: auto;
  }

  .doc-layout {
    grid-template-columns: 1fr;
  }

  .doc-header--banner {
    margin: -24px -24px 20px;
    padding: 22px 24px;
  }
}
</style>
