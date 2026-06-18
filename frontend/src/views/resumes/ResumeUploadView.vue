<template>
  <div>
    <PageHeader title="文件生成简历" description="上传 PDF（文字版/扫描版）、Word、文本或图片，解析为可编辑表单。">
      <template #actions>
        <el-button type="primary" :loading="parsing" :disabled="!selectedFile" @click="parse">解析为表单</el-button>
        <ResumeExportToolbar
          v-if="formReady"
          v-model:template-id="templateId"
          :snapshot="previewSnapshot"
          :preview-ref="previewComponent"
          :filename="exportFilename"
        />
        <el-button :disabled="!formReady" :loading="saving" @click="saveResume">保存为简历</el-button>
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <el-upload
          drag
          action="#"
          :auto-upload="false"
          accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp"
          :limit="1"
          :show-file-list="false"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽或点击上传简历文件</div>
          <div class="el-upload__tip">支持 PDF、DOCX、TXT、MD、PNG、JPG、WEBP</div>
        </el-upload>

        <div v-if="selectedFile" class="file-card">
          <div class="file-card__main">
            <strong>{{ selectedFile.name }}</strong>
            <span>{{ formatSize(selectedFile.size) }}</span>
          </div>
          <el-button link type="danger" @click="clearFile">移除文件</el-button>
        </div>

        <el-alert
          class="format-tip"
          type="info"
          :closable="false"
          title="文件说明"
          description="PDF 优先提取文字层；扫描版 PDF 和图片需要本机 OCR 环境。Word 仅支持 .docx，也可上传 TXT/MD 先跑通演示链路。"
        />

        <el-collapse v-if="extractInfo.sourceType" class="extract-info">
          <el-collapse-item title="解析信息" name="meta">
            <div class="meta-row">
              <span>来源类型</span>
              <el-tag type="success">{{ sourceTypeLabel }}</el-tag>
            </div>
            <div v-if="extractInfo.fileName" class="meta-row">
              <span>文件名</span>
              <span>{{ extractInfo.fileName }}</span>
            </div>
          </el-collapse-item>
        </el-collapse>
      </section>

      <section class="panel">
        <div class="panel-title">
          <h2>简历表单与预览</h2>
          <el-tag v-if="formReady" type="success">可编辑</el-tag>
        </div>
        <el-empty v-if="!formReady" description="上传文件后点击「解析为表单」" />
        <template v-else>
          <ResumeFormEditor v-model:active-tab="activeTab" :form-api="formApi" />
          <div class="preview-block">
            <div class="panel-title compact">
              <h3>模板预览</h3>
              <el-tag type="info">{{ currentTemplate.name }}</el-tag>
            </div>
            <div class="preview-shell">
              <ResumeStyledPreview ref="previewComponent" :snapshot="previewSnapshot" :template-id="templateId" />
            </div>
          </div>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { UploadFilled } from "@element-plus/icons-vue";
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { aiApi, resumeApi } from "@/api/modules";
import PageHeader from "@/components/PageHeader.vue";
import ResumeExportToolbar from "@/components/ResumeExportToolbar.vue";
import ResumeFormEditor from "@/components/ResumeFormEditor.vue";
import ResumeStyledPreview from "@/components/ResumeStyledPreview.vue";
import { useResumeForm } from "@/composables/useResumeForm";
import { buildExportFilename } from "@/utils/resumeExport";
import { DEFAULT_RESUME_TEMPLATE_ID, getTemplatePreset, type ResumeTemplateId } from "@/utils/resumeTemplates";

const router = useRouter();
const selectedFile = ref<File | null>(null);
const activeTab = ref("basic");
const parsing = ref(false);
const saving = ref(false);
const formReady = ref(false);
const templateId = ref<ResumeTemplateId>(DEFAULT_RESUME_TEMPLATE_ID);
const previewComponent = ref<InstanceType<typeof ResumeStyledPreview>>();

const extractInfo = reactive({
  fileName: "",
  sourceType: ""
});

const formApi = useResumeForm();
const { fillForm, packStoredContent, exportSnapshot, resetForm } = formApi;

const previewSnapshot = computed(() => exportSnapshot());
const currentTemplate = computed(() => getTemplatePreset(templateId.value));
const exportFilename = computed(() => buildExportFilename(previewSnapshot.value));

const sourceTypeLabel = computed(() => {
  switch (extractInfo.sourceType) {
    case "pdf-text":
      return "PDF 文字版";
    case "pdf-ocr":
      return "PDF 扫描版（OCR）";
    case "docx":
      return "Word 文档";
    case "plain-text":
      return "文本文件";
    case "image-ocr":
      return "图片 OCR";
    default:
      return extractInfo.sourceType || "未知";
  }
});

function formatSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function handleFileChange(file: UploadFile) {
  if (!file.raw) return;
  selectedFile.value = file.raw;
  formReady.value = false;
  extractInfo.fileName = "";
  extractInfo.sourceType = "";
  resetForm();
}

function handleExceed() {
  ElMessage.warning("一次只能上传一个文件，请先移除当前文件");
}

function clearFile() {
  selectedFile.value = null;
  formReady.value = false;
  extractInfo.fileName = "";
  extractInfo.sourceType = "";
  resetForm();
}

async function parse() {
  if (!selectedFile.value) {
    ElMessage.warning("请先上传简历文件");
    return;
  }
  parsing.value = true;
  formReady.value = false;
  extractInfo.fileName = "";
  extractInfo.sourceType = "";
  try {
    const result = await aiApi.parseResumeUpload(selectedFile.value);
    fillForm(result.data);
    extractInfo.fileName = String(result.data.file_name || selectedFile.value.name);
    extractInfo.sourceType = String(result.data.source_type || "");
    const hasContent = Boolean(
      formApi.resumeForm.basic_info.name ||
        formApi.resumeForm.summary ||
        formApi.resumeForm.education.some((item) => item.school || item.major)
    );
    if (!hasContent) {
      ElMessage.warning("文件已解析，但结构化字段较少，请手动补充表单");
    } else {
      ElMessage.success("已解析为可编辑表单");
    }
    formReady.value = true;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "解析失败");
  } finally {
    parsing.value = false;
  }
}

async function saveResume() {
  if (!formReady.value) return;
  saving.value = true;
  try {
    const title = formApi.resumeForm.basic_info.name
      ? `${formApi.resumeForm.basic_info.name}的简历`
      : selectedFile.value?.name.replace(/\.[^.]+$/, "") || "文件解析简历";
    const resume = await resumeApi.create({
      title,
      content: packStoredContent(templateId.value),
      is_default: true
    });
    ElMessage.success("已保存到简历列表");
    router.push({ name: "resume-edit", params: { id: resume.id } });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.file-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: #f8fafc;
}

.file-card__main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.file-card__main strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-card__main span {
  font-size: 12px;
  color: #6b7280;
}

.format-tip {
  margin-top: 16px;
}

.extract-info {
  margin-top: 16px;
}

.meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 0;
  font-size: 13px;
}

.preview-block {
  margin-top: 18px;
}

.panel-title.compact h3 {
  margin: 0;
  font-size: 16px;
}

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
</style>
