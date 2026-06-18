<template>
  <div>
    <PageHeader title="文字生成简历" description="根据自然语言描述生成可编辑表单，选择模板后可保存或导出。">
      <template #actions>
        <el-button type="primary" :loading="generating" @click="generate">生成表单</el-button>
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
        <el-form label-position="top">
          <el-form-item label="个人描述">
            <el-input
              v-model="text"
              type="textarea"
              :rows="22"
              placeholder="粘贴姓名、联系方式、教育经历、技能、实习经历、项目经历等内容。"
            />
          </el-form-item>
        </el-form>
      </section>

      <section class="panel">
        <div class="panel-title">
          <h2>简历表单与预览</h2>
          <el-tag v-if="formReady" type="success">可编辑</el-tag>
        </div>
        <el-empty v-if="!formReady" description="输入描述后生成可编辑表单" />
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
import { ElMessage } from "element-plus";
import { computed, ref } from "vue";
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
const text = ref("");
const activeTab = ref("basic");
const generating = ref(false);
const saving = ref(false);
const formReady = ref(false);
const templateId = ref<ResumeTemplateId>(DEFAULT_RESUME_TEMPLATE_ID);
const previewComponent = ref<InstanceType<typeof ResumeStyledPreview>>();

const formApi = useResumeForm();
const { fillForm, packStoredContent, exportSnapshot } = formApi;

const previewSnapshot = computed(() => exportSnapshot());
const currentTemplate = computed(() => getTemplatePreset(templateId.value));
const exportFilename = computed(() => buildExportFilename(previewSnapshot.value));

async function generate() {
  if (!text.value.trim()) {
    ElMessage.warning("请先输入个人经历描述");
    return;
  }
  generating.value = true;
  try {
    const result = await aiApi.generateResume(text.value);
    fillForm(result.data);
    formReady.value = true;
    ElMessage.success("表单已生成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "生成失败");
  } finally {
    generating.value = false;
  }
}

async function saveResume() {
  if (!formReady.value) return;
  saving.value = true;
  try {
    const title = formApi.resumeForm.basic_info.name ? `${formApi.resumeForm.basic_info.name}的简历` : "AI 生成简历";
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