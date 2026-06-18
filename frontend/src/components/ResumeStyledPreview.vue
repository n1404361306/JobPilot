<template>
  <article ref="rootRef" class="resume-doc" :class="`resume-doc--${templateId}`" :style="accentStyle">
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

    <template v-else>
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
import { getTemplatePreset, type ResumeTemplateId } from "@/utils/resumeTemplates";

const props = withDefaults(
  defineProps<{
    snapshot: ResumeFormSnapshot;
    templateId?: ResumeTemplateId;
  }>(),
  {
    templateId: "classic"
  }
);

const rootRef = ref<HTMLElement>();
const preset = computed(() => getTemplatePreset(props.templateId));
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
