<template>
  <el-dialog
    :model-value="visible"
    :title="`选择模板 · ${resume?.title || ''}`"
    width="960px"
    destroy-on-close
    class="template-dialog"
    @close="emit('update:visible', false)"
  >
    <div v-if="loading" class="dialog-loading">
      <el-skeleton :rows="6" animated />
    </div>
    <template v-else>
      <div class="template-picker">
        <button
          v-for="preset in RESUME_TEMPLATE_PRESETS"
          :key="preset.id"
          type="button"
          class="template-chip"
          :class="{ active: templateId === preset.id }"
          @click="templateId = preset.id"
        >
          <span class="template-dot" :style="{ background: preset.accent }" />
          <span class="template-name">{{ preset.name }}</span>
          <span class="template-desc">{{ preset.description }}</span>
        </button>
      </div>

      <div v-if="customTemplates.length" class="custom-template-block">
        <div class="block-title">用户上传模板</div>
        <div class="template-picker">
          <button
            v-for="template in customTemplates"
            :key="template.id"
            type="button"
            class="template-chip"
            :class="{ active: templateId === customTemplateId(template.id) }"
            @click="templateId = customTemplateId(template.id)"
          >
            <span class="template-dot custom-dot" />
            <span class="template-name">{{ template.name }}</span>
            <span class="template-desc">
              {{ template.description || "用户上传模板" }} · {{ template.is_public ? "公开" : "私有" }}
            </span>
          </button>
        </div>
      </div>
      <el-alert
        v-else
        type="info"
        :closable="false"
        show-icon
        title="暂无用户上传模板"
        description="可在「模板选择」页上传，或使用 AI 制作模板。"
        class="custom-empty-alert"
      />

      <div class="dialog-toolbar">
        <ResumeExportToolbar
          hide-template-select
          :snapshot="previewSnapshot"
          :preview-ref="previewComponent"
          :filename="exportFilename"
        />
      </div>

      <div class="preview-shell">
        <ResumeStyledPreview
          ref="previewComponent"
          :snapshot="previewSnapshot"
          :template-id="templateId"
          :custom-template-content="selectedCustomTemplateContent"
        />
      </div>
    </template>

    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="applyTemplate">应用模板</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, ref, watch } from "vue";
import { resumeApi, templateApi } from "@/api/modules";
import type { Resume, ResumeTemplate } from "@/api/types";
import ResumeExportToolbar from "@/components/ResumeExportToolbar.vue";
import ResumeStyledPreview from "@/components/ResumeStyledPreview.vue";
import { getResumeDisplayContent, getResumeSnapshot, getResumeTemplateId } from "@/composables/useResumeForm";
import { buildExportFilename } from "@/utils/resumeExport";
import { snapshotFromPlainText } from "@/utils/resumeHelpers";
import {
  customTemplateId,
  DEFAULT_RESUME_TEMPLATE_ID,
  filterSelectableCustomTemplates,
  findCustomTemplateContent,
  RESUME_TEMPLATE_PRESETS,
  type ResumeTemplateId
} from "@/utils/resumeTemplates";

const props = defineProps<{
  visible: boolean;
  resume: Resume | null;
}>();

const emit = defineEmits<{
  "update:visible": [value: boolean];
  applied: [];
}>();

const loading = ref(false);
const saving = ref(false);
const templateId = ref<ResumeTemplateId>(DEFAULT_RESUME_TEMPLATE_ID);
const previewComponent = ref<InstanceType<typeof ResumeStyledPreview>>();
const resumeContent = ref("");
const customTemplates = ref<ResumeTemplate[]>([]);

const previewSnapshot = computed(() => {
  const snapshot = getResumeSnapshot(resumeContent.value);
  if (snapshot) return snapshot;
  return snapshotFromPlainText(getResumeDisplayContent(resumeContent.value));
});

const exportFilename = computed(() => buildExportFilename(previewSnapshot.value, props.resume?.title || "resume"));
const selectedCustomTemplateContent = computed(() =>
  findCustomTemplateContent(customTemplates.value, templateId.value)
);

watch(
  () => [props.visible, props.resume?.id] as const,
  async ([visible, resumeId]) => {
    if (!visible || !resumeId || !props.resume) {
      return;
    }
    loading.value = true;
    try {
      const [resume, templates] = await Promise.all([
        props.resume.id === resumeId ? props.resume : resumeApi.get(resumeId),
        templateApi.list()
      ]);
      resumeContent.value = resume.content;
      templateId.value = getResumeTemplateId(resume.content);
      customTemplates.value = filterSelectableCustomTemplates(templates);
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : "简历加载失败");
      emit("update:visible", false);
    } finally {
      loading.value = false;
    }
  },
  { immediate: true }
);

async function applyTemplate() {
  if (!props.resume) return;
  saving.value = true;
  try {
    const resume = await resumeApi.selectTemplate(props.resume.id, templateId.value);
    resumeContent.value = resume.content;
    ElMessage.success("模板已应用");
    emit("applied");
    emit("update:visible", false);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "模板应用失败");
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.dialog-loading {
  padding: 12px 0;
}

.template-picker {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.template-chip {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  gap: 4px 10px;
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.template-chip:hover {
  border-color: #93c5fd;
}

.template-chip.active {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.12);
}

.template-dot {
  grid-row: 1 / span 2;
  width: 12px;
  height: 12px;
  margin-top: 4px;
  border-radius: 50%;
}

.template-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.template-desc {
  grid-column: 2;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
}

.dialog-toolbar {
  margin-bottom: 14px;
}

.custom-template-block {
  margin-top: 4px;
}

.custom-empty-alert {
  margin: 8px 0 12px;
}

.block-title {
  margin: 4px 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
}

.custom-dot {
  background: linear-gradient(135deg, #f59e0b, #2563eb);
}

.preview-shell {
  max-height: 460px;
  overflow: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
}

.preview-shell :deep(.resume-doc) {
  margin: 0 auto;
  max-width: 820px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

@media (max-width: 760px) {
  .template-picker {
    grid-template-columns: 1fr;
  }
}
</style>
