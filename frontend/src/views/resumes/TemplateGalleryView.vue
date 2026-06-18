<template>
  <div>
    <PageHeader title="简历模板库" description="内置预设与用户模板统一预览，可在编辑页套用并导出。">
      <template #actions>
        <el-button :icon="Download" @click="downloadExample">下载示例</el-button>
        <el-button :icon="Document" @click="openTemplateDoc">要求文档</el-button>
        <el-button :icon="MagicStick" @click="router.push({ name: 'template-ai-maker' })">AI 制作</el-button>
        <el-button :icon="Upload" type="primary" @click="uploadDialogVisible = true">上传模板</el-button>
      </template>
    </PageHeader>

    <section class="panel template-section">
      <div class="section-head">
        <h2>系统模板</h2>
        <el-tag size="small" type="info">4 套内置</el-tag>
      </div>
      <div class="template-grid">
        <article v-for="preset in RESUME_TEMPLATE_PRESETS" :key="preset.id" class="template-card">
          <div class="template-card-head">
            <div class="template-title-wrap">
              <span class="template-dot" :style="{ background: preset.accent }" />
              <div>
                <h3>{{ preset.name }}</h3>
                <p>{{ preset.description }}</p>
              </div>
            </div>
            <el-tag size="small" effect="plain">系统</el-tag>
          </div>
          <div class="template-preview">
            <ResumeTemplateThumbnail :snapshot="sampleSnapshot" :template-id="preset.id" />
          </div>
          <div class="template-card-foot">
            <el-button size="small" type="primary" @click="createWithPreset(preset.id)">新建并使用</el-button>
          </div>
        </article>
      </div>
    </section>

    <section v-if="userTemplates.length" class="panel template-section">
      <div class="section-head">
        <h2>用户模板</h2>
        <el-tag size="small" type="info">HTML / 文本</el-tag>
      </div>
      <div class="template-grid">
        <article v-for="template in userTemplates" :key="template.id" class="template-card">
          <div class="template-card-head">
            <div class="template-title-wrap">
              <span class="template-dot custom-dot" />
              <div>
                <h3>{{ template.name }}</h3>
                <p>{{ template.description || "用户上传模板" }}</p>
              </div>
            </div>
            <div class="tag-row">
              <el-tag v-if="template.enabled" size="small" type="success">启用</el-tag>
              <el-tag size="small" :type="template.is_public ? 'warning' : 'info'">
                {{ template.is_public ? "公开" : "私有" }}
              </el-tag>
            </div>
          </div>
          <div class="template-preview">
            <ResumeTemplateThumbnail
              :snapshot="sampleSnapshot"
              :template-id="customTemplateId(template.id)"
              :custom-template-content="template.content"
            />
          </div>
          <div class="template-card-foot">
            <el-button size="small" type="primary" @click="createWithTemplate(template)">新建并使用</el-button>
            <el-button v-if="canEditTemplate(template)" size="small" text type="primary" @click="editTemplate(template.id)">
              编辑
            </el-button>
          </div>
        </article>
      </div>
    </section>

    <section v-if="!loading && !userTemplates.length" class="panel template-section">
      <EmptyState description="暂无用户模板，可使用上方系统模板，或通过 AI / 上传创建" />
    </section>

    <el-dialog v-model="uploadDialogVisible" title="上传自定义模板" width="640px">
      <el-form label-position="top">
        <el-form-item label="模板名称">
          <el-input v-model="uploadForm.name" placeholder="例如：单栏技术岗模板" />
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input v-model="uploadForm.description" placeholder="说明适用场景、风格或注意事项" />
        </el-form-item>
        <el-form-item label="可见性">
          <el-radio-group v-model="uploadForm.is_public">
            <el-radio-button :value="false">仅自己使用</el-radio-button>
            <el-radio-button :value="true">公开给其他用户</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="模板文件">
          <el-upload
            action="#"
            drag
            :auto-upload="false"
            accept=".html,.htm,.txt"
            :on-change="selectTemplateFile"
            :limit="1"
            :show-file-list="true"
          >
            <el-icon class="el-icon--upload"><Upload /></el-icon>
            <div class="el-upload__text">拖拽或点击选择 HTML / TXT 模板</div>
            <div class="el-upload__tip">
              建议小于 256KB。可先
              <el-link type="primary" @click="downloadExample">下载示例模板</el-link>
              参考
            </div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="uploadTemplate">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Document, Download, MagicStick, Upload } from "@element-plus/icons-vue";
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { templateApi } from "@/api/modules";
import type { ResumeTemplate } from "@/api/types";
import EmptyState from "@/components/EmptyState.vue";
import PageHeader from "@/components/PageHeader.vue";
import ResumeTemplateThumbnail from "@/components/ResumeTemplateThumbnail.vue";
import { useUserStore } from "@/stores/user";
import { createSampleSnapshot } from "@/utils/resumeHelpers";
import { customTemplateId, filterSelectableCustomTemplates, RESUME_TEMPLATE_PRESETS, type BuiltInResumeTemplateId } from "@/utils/resumeTemplates";

const router = useRouter();
const userStore = useUserStore();
const loading = ref(true);
const uploading = ref(false);
const uploadDialogVisible = ref(false);
const userTemplates = ref<ResumeTemplate[]>([]);
const sampleSnapshot = createSampleSnapshot();
const selectedFile = ref<File | null>(null);
const uploadForm = reactive({
  name: "",
  description: "",
  is_public: false
});

async function load() {
  try {
    userTemplates.value = filterSelectableCustomTemplates(await templateApi.list());
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "模板加载失败");
  } finally {
    loading.value = false;
  }
}

function selectTemplateFile(file: UploadFile) {
  selectedFile.value = file.raw || null;
  if (!uploadForm.name && file.name) {
    uploadForm.name = file.name.replace(/\.(html?|txt)$/i, "");
  }
}

function resetUploadForm() {
  selectedFile.value = null;
  Object.assign(uploadForm, { name: "", description: "", is_public: false });
}

function openTemplateDoc() {
  window.open("/docs/resume_template_requirements.html", "_blank");
}

function downloadExample() {
  const link = document.createElement("a");
  link.href = "/docs/resume_template_example.html";
  link.download = "resume_template_example.html";
  link.rel = "noopener";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function createWithPreset(id: BuiltInResumeTemplateId) {
  router.push({ name: "resume-new", query: { template: id } });
}

function createWithTemplate(template: ResumeTemplate) {
  router.push({ name: "resume-new", query: { template: customTemplateId(template.id) } });
}

function editTemplate(id: number) {
  router.push({ name: "template-ai-maker", query: { id: String(id) } });
}

function canEditTemplate(template: ResumeTemplate) {
  return template.user_id != null && template.user_id === userStore.profile?.id;
}

async function uploadTemplate() {
  if (!selectedFile.value) {
    ElMessage.warning("请选择模板文件");
    return;
  }
  uploading.value = true;
  try {
    await templateApi.upload(selectedFile.value, uploadForm);
    ElMessage.success("模板已上传");
    uploadDialogVisible.value = false;
    resetUploadForm();
    await load();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "上传失败");
  } finally {
    uploading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.template-section {
  margin-bottom: 14px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.section-head h2 {
  margin: 0;
  font-size: 16px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.template-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
}

.template-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  min-height: 52px;
}

.template-title-wrap {
  display: flex;
  gap: 8px;
  min-width: 0;
}

.template-title-wrap h3 {
  margin: 0;
  font-size: 14px;
  line-height: 1.3;
}

.template-title-wrap p {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.template-dot {
  width: 10px;
  height: 10px;
  margin-top: 4px;
  border-radius: 50%;
  flex-shrink: 0;
}

.custom-dot {
  background: linear-gradient(135deg, #f59e0b, #2563eb);
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 4px;
}

.template-preview {
  min-height: 0;
}

.template-card-foot {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
  min-height: 28px;
}

@media (max-width: 760px) {
  .template-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}
</style>
