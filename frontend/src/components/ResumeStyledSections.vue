<template>
  <div class="styled-sections" :class="`styled-sections--${variant}`">
    <section v-if="hasText(snapshot.summary)" class="doc-section">
      <h2 class="doc-section-title">个人简介</h2>
      <p class="doc-section-text">{{ snapshot.summary }}</p>
    </section>

    <section v-if="showSkills && skillGroupsList.length" class="doc-section">
      <h2 class="doc-section-title">专业技能</h2>
      <div class="doc-skill-grid">
        <div v-for="item in skillGroupsList" :key="item.label" class="doc-skill-item">
          <span class="doc-skill-label">{{ item.label }}</span>
          <span>{{ item.value.replace(/\n/g, " · ") }}</span>
        </div>
      </div>
    </section>

    <section v-if="educationItems.length" class="doc-section">
      <h2 class="doc-section-title">教育经历</h2>
      <article v-for="(item, index) in educationItems" :key="index" class="doc-entry">
        <div class="doc-entry-head">
          <strong>{{ item.school }} · {{ item.major }}</strong>
          <span>{{ item.period }}</span>
        </div>
        <div class="doc-entry-meta">{{ item.degree }}<template v-if="hasText(item.research_direction)"> · {{ item.research_direction }}</template></div>
        <p v-if="hasText(item.gpa)" class="doc-entry-sub">GPA：{{ item.gpa }}</p>
        <ul v-if="textLines(item.highlightsText).length" class="doc-bullets">
          <li v-for="(line, lineIndex) in textLines(item.highlightsText)" :key="lineIndex">{{ line }}</li>
        </ul>
      </article>
    </section>

    <section v-if="internshipItems.length" class="doc-section">
      <h2 class="doc-section-title">实习经历</h2>
      <article v-for="(item, index) in internshipItems" :key="index" class="doc-entry">
        <div class="doc-entry-head">
          <strong>{{ item.company }} · {{ item.position }}</strong>
          <span>{{ item.period }}</span>
        </div>
        <div v-if="hasText(item.location)" class="doc-entry-meta">{{ item.location }}</div>
        <p v-if="hasText(item.description)" class="doc-section-text">{{ item.description }}</p>
        <ul v-if="textLines(item.responsibilitiesText).length" class="doc-bullets">
          <li v-for="(line, lineIndex) in textLines(item.responsibilitiesText)" :key="lineIndex">{{ line }}</li>
        </ul>
        <p v-if="hasText(item.techStackText)" class="doc-entry-sub">技术栈：{{ item.techStackText.replace(/\n/g, " · ") }}</p>
      </article>
    </section>

    <section v-if="projectItems.length" class="doc-section">
      <h2 class="doc-section-title">项目经历</h2>
      <article v-for="(item, index) in projectItems" :key="index" class="doc-entry">
        <div class="doc-entry-head">
          <strong>{{ item.project_name }}</strong>
          <span>{{ item.period }}</span>
        </div>
        <div v-if="hasText(item.type)" class="doc-entry-meta">{{ item.type }}</div>
        <p v-if="hasText(item.description)" class="doc-section-text">{{ item.description }}</p>
        <ul v-if="textLines(item.responsibilitiesText).length" class="doc-bullets">
          <li v-for="(line, lineIndex) in textLines(item.responsibilitiesText)" :key="lineIndex">{{ line }}</li>
        </ul>
        <p v-if="hasText(item.techStackText)" class="doc-entry-sub">技术栈：{{ item.techStackText.replace(/\n/g, " · ") }}</p>
        <ul v-if="textLines(item.resultsText).length" class="doc-bullets doc-bullets--result">
          <li v-for="(line, lineIndex) in textLines(item.resultsText)" :key="lineIndex">{{ line }}</li>
        </ul>
      </article>
    </section>

    <section v-if="otherItems.length" class="doc-section">
      <h2 class="doc-section-title">其他</h2>
      <div v-for="item in otherItems" :key="item.label" class="doc-other">
        <strong>{{ item.label }}</strong>
        <p>{{ item.value }}</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ResumeFormSnapshot } from "@/composables/useResumeForm";
import { hasText, skillGroups, textLines } from "@/utils/resumeHelpers";

const props = withDefaults(
  defineProps<{
    snapshot: ResumeFormSnapshot;
    showSkills?: boolean;
    variant?: "default" | "minimal";
  }>(),
  {
    showSkills: true,
    variant: "default"
  }
);

const skillGroupsList = computed(() => skillGroups(props.snapshot));

const educationItems = computed(() =>
  props.snapshot.education.filter((item) => hasText(item.school) || hasText(item.major))
);

const internshipItems = computed(() =>
  props.snapshot.internships.filter((item) => hasText(item.company) || hasText(item.position))
);

const projectItems = computed(() =>
  props.snapshot.projects.filter((item) => hasText(item.project_name) || hasText(item.description))
);

const otherItems = computed(() =>
  [
    { label: "科研经历", value: props.snapshot.researchText },
    { label: "获奖经历", value: props.snapshot.awardsText },
    { label: "证书", value: props.snapshot.certificatesText },
    { label: "开源贡献", value: props.snapshot.open_source },
    { label: "兴趣方向", value: props.snapshot.interests },
    { label: "个人评价", value: props.snapshot.self_evaluation }
  ].filter((item) => hasText(item.value))
);
</script>

<style scoped>
.styled-sections {
  --accent: inherit;
}

.doc-section {
  margin-bottom: 22px;
}

.doc-section-title {
  margin: 0 0 12px;
  padding-bottom: 6px;
  font-size: 15px;
  font-weight: 700;
  color: var(--accent, #1e3a5f);
  border-bottom: 2px solid var(--accent-soft, #dbeafe);
}

.styled-sections--minimal .doc-section-title {
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  border-bottom: 1px solid #e5e7eb;
  color: #6b7280;
}

.doc-section-text {
  margin: 0;
  font-size: 13px;
  color: #374151;
  white-space: pre-wrap;
}

.doc-skill-grid {
  display: grid;
  gap: 8px;
}

.doc-skill-item {
  display: grid;
  grid-template-columns: 108px 1fr;
  gap: 10px;
  font-size: 13px;
}

.doc-skill-label {
  font-weight: 600;
  color: #374151;
}

.doc-entry {
  margin-bottom: 16px;
}

.doc-entry-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 14px;
}

.doc-entry-head span {
  flex-shrink: 0;
  font-size: 12px;
  color: #6b7280;
}

.doc-entry-meta,
.doc-entry-sub {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.doc-bullets {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 13px;
  color: #374151;
}

.doc-bullets li {
  margin-bottom: 4px;
}

.doc-other {
  margin-bottom: 10px;
  font-size: 13px;
}

.doc-other strong {
  display: block;
  margin-bottom: 4px;
  color: #374151;
}

.doc-other p {
  margin: 0;
  color: #4b5563;
  white-space: pre-wrap;
}
</style>
