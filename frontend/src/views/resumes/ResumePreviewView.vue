<template>
  <div>
    <PageHeader title="简历预览和导出" description="选择预设模板，预览排版效果并导出 PDF 或 DOCX 文件。">
      <template #actions>
        <el-button :icon="Printer" @click="printPage">打印</el-button>
        <ResumeExportToolbar
          v-model:template-id="templateId"
          :snapshot="previewSnapshot"
          :preview-ref="previewComponent"
          :filename="exportFilename"
        />
      </template>
    </PageHeader>

    <section class="panel">
      <el-skeleton v-if="loading" :rows="8" animated />
      <div v-else class="preview-shell">
        <ResumeStyledPreview
          ref="previewComponent"
          :snapshot="previewSnapshot"
          :template-id="templateId"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Printer } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { resumeApi } from "@/api/modules";
import type { Resume } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import ResumeExportToolbar from "@/components/ResumeExportToolbar.vue";
import ResumeStyledPreview from "@/components/ResumeStyledPreview.vue";
import { getResumeDisplayContent, getResumeSnapshot, getResumeTemplateId } from "@/composables/useResumeForm";
import { buildExportFilename } from "@/utils/resumeExport";
import { snapshotFromPlainText } from "@/utils/resumeHelpers";
import { DEFAULT_RESUME_TEMPLATE_ID, type ResumeTemplateId } from "@/utils/resumeTemplates";

const route = useRoute();
const loading = ref(true);
const resume = ref<Resume | null>(null);
const previewComponent = ref<InstanceType<typeof ResumeStyledPreview>>();
const templateId = ref<ResumeTemplateId>(DEFAULT_RESUME_TEMPLATE_ID);

const previewSnapshot = computed(() => {
  const content = resume.value?.content || "";
  return getResumeSnapshot(content) ?? snapshotFromPlainText(getResumeDisplayContent(content));
});

const exportFilename = computed(() => buildExportFilename(previewSnapshot.value, resume.value?.title || "resume"));

function printPage() {
  window.print();
}

onMounted(async () => {
  try {
    resume.value = await resumeApi.get(Number(route.params.id));
    templateId.value = getResumeTemplateId(resume.value.content);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "简历加载失败");
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.preview-shell {
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

@media print {
  .preview-shell {
    border: none;
    background: #fff;
  }

  .preview-shell :deep(.resume-doc) {
    box-shadow: none;
    max-width: none;
  }
}
</style>
