<template>
  <div>
    <PageHeader title="简历模板库" description="内置 4 套精美预设模板，可在编辑页直接套用并导出 PDF / DOCX。">
      <template #actions>
        <el-upload action="#" :auto-upload="false" accept=".html,.htm,.txt" :on-change="uploadTemplate" :show-file-list="false">
          <el-button :icon="Upload">上传自定义模板</el-button>
        </el-upload>
      </template>
    </PageHeader>

    <section class="grid-2 preset-grid">
      <article v-for="preset in RESUME_TEMPLATE_PRESETS" :key="preset.id" class="panel preset-card">
        <div class="panel-title">
          <div>
            <h2>{{ preset.name }}</h2>
            <p class="preset-desc">{{ preset.description }}</p>
          </div>
          <span class="preset-dot" :style="{ background: preset.accent }" />
        </div>
        <div class="preview-shell">
          <ResumeStyledPreview :snapshot="sampleSnapshot" :template-id="preset.id" />
        </div>
        <div class="preset-actions">
          <el-button type="primary" @click="router.push({ name: 'resume-new' })">新建并使用</el-button>
        </div>
      </article>
    </section>

    <section v-if="templates.length" class="panel custom-section">
      <div class="panel-title">
        <h2>用户上传模板</h2>
        <el-tag type="info">HTML / 文本</el-tag>
      </div>
      <div class="grid-3">
        <article v-for="template in templates" :key="template.id" class="panel inner-panel">
          <div class="panel-title">
            <h3>{{ template.name }}</h3>
            <el-tag v-if="template.enabled" type="success">启用</el-tag>
          </div>
          <p>{{ template.description || "暂无描述" }}</p>
          <div class="resume-preview template-preview">{{ template.content }}</div>
        </article>
      </div>
    </section>

    <section v-if="!loading && !templates.length" class="panel custom-section">
      <EmptyState description="暂无用户上传模板，可直接使用上方预设模板" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { Upload } from "@element-plus/icons-vue";
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { templateApi } from "@/api/modules";
import type { ResumeTemplate } from "@/api/types";
import EmptyState from "@/components/EmptyState.vue";
import PageHeader from "@/components/PageHeader.vue";
import ResumeStyledPreview from "@/components/ResumeStyledPreview.vue";
import { createSampleSnapshot } from "@/utils/resumeHelpers";
import { RESUME_TEMPLATE_PRESETS } from "@/utils/resumeTemplates";

const router = useRouter();
const loading = ref(true);
const templates = ref<ResumeTemplate[]>([]);
const sampleSnapshot = createSampleSnapshot();

async function load() {
  try {
    templates.value = await templateApi.list();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "模板加载失败");
  } finally {
    loading.value = false;
  }
}

async function uploadTemplate(file: UploadFile) {
  if (!file.raw) return;
  try {
    await templateApi.upload(file.raw);
    ElMessage.success("模板已上传");
    await load();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "上传失败");
  }
}

onMounted(load);
</script>

<style scoped>
.preset-grid {
  margin-bottom: 18px;
}

.preset-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.preset-desc {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.preset-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.preview-shell {
  overflow: hidden;
  max-height: 420px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
}

.preview-shell :deep(.resume-doc) {
  transform: scale(0.72);
  transform-origin: top center;
  margin: 0 auto -180px;
  max-width: 820px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.preset-actions {
  display: flex;
  justify-content: flex-end;
}

.custom-section {
  margin-top: 8px;
}

.inner-panel h3 {
  margin: 0;
  font-size: 16px;
}

.template-preview {
  min-height: 180px;
  max-height: 220px;
  overflow: hidden;
  margin-top: 14px;
  font-size: 13px;
}
</style>
