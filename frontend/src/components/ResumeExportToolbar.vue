<template>
  <div class="export-toolbar">
    <el-select
      v-if="!hideTemplateSelect"
      v-model="templateId"
      placeholder="选择模板"
      class="template-select"
      filterable
    >
      <el-option-group label="内置模板">
        <el-option v-for="item in RESUME_TEMPLATE_PRESETS" :key="item.id" :label="item.name" :value="item.id">
          <div class="template-option">
            <span>{{ item.name }}</span>
            <span class="template-dot" :style="{ background: item.accent }" />
          </div>
        </el-option>
      </el-option-group>
      <el-option-group v-if="customTemplates.length" label="用户模板">
        <el-option
          v-for="item in customTemplates"
          :key="item.id"
          :label="`${item.name}${item.is_public ? '（公开）' : ''}`"
          :value="customTemplateId(item.id)"
        />
      </el-option-group>
    </el-select>
    <el-button :icon="Download" :loading="exportingPdf" @click="handleExportPdf">导出 PDF</el-button>
    <el-button :icon="Document" :loading="exportingDocx" @click="handleExportDocx">导出 DOCX</el-button>
  </div>
</template>

<script setup lang="ts">
import { Document, Download } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { ref } from "vue";
import type { ResumeTemplate } from "@/api/types";
import type { ResumeFormSnapshot } from "@/composables/useResumeForm";
import { buildExportFilename, exportResumeDocx, exportResumePdf } from "@/utils/resumeExport";
import {
  customTemplateId,
  DEFAULT_RESUME_TEMPLATE_ID,
  isCustomTemplateId,
  RESUME_TEMPLATE_PRESETS,
  type ResumeTemplateId
} from "@/utils/resumeTemplates";

const templateId = defineModel<ResumeTemplateId>("templateId", { default: DEFAULT_RESUME_TEMPLATE_ID });

const props = withDefaults(
  defineProps<{
    snapshot: ResumeFormSnapshot;
    previewRef?: { getElement?: () => HTMLElement | undefined } | HTMLElement | null;
    filename?: string;
    customTemplates?: ResumeTemplate[];
    hideTemplateSelect?: boolean;
  }>(),
  {
    customTemplates: () => [],
    hideTemplateSelect: false
  }
);

const exportingPdf = ref(false);
const exportingDocx = ref(false);

function resolvePreviewElement() {
  const target = props.previewRef;
  if (!target) return null;
  if (target instanceof HTMLElement) return target;
  return target.getElement?.() ?? null;
}

async function handleExportPdf() {
  const element = resolvePreviewElement();
  if (!element) {
    ElMessage.warning("预览区域未就绪");
    return;
  }
  exportingPdf.value = true;
  try {
    await exportResumePdf(element, props.filename || buildExportFilename(props.snapshot));
    ElMessage.success("PDF 已下载");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "PDF 导出失败");
  } finally {
    exportingPdf.value = false;
  }
}

async function handleExportDocx() {
  if (isCustomTemplateId(templateId.value)) {
    ElMessage.warning("自定义模板请使用 PDF 导出，或在预览页面直接打印");
    return;
  }
  exportingDocx.value = true;
  try {
    await exportResumeDocx(props.snapshot, templateId.value, props.filename || buildExportFilename(props.snapshot));
    ElMessage.success("DOCX 已下载");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "DOCX 导出失败");
  } finally {
    exportingDocx.value = false;
  }
}
</script>

<style scoped>
.export-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.template-select {
  width: 220px;
}

.template-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.template-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
</style>
