<template>
  <div>
    <PageHeader :title="isEdit ? '简历编辑器' : '新建简历'" description="使用表单分段编辑简历内容，右侧实时预览最终排版效果。">
      <template #actions>
        <el-button @click="router.push({ name: 'resume-list' })">返回列表</el-button>
        <ResumeExportToolbar
          v-model:template-id="templateId"
          :custom-templates="customTemplates"
          :snapshot="previewSnapshot"
          :preview-ref="previewComponent"
          :filename="exportFilename"
        />
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <el-form ref="metaFormRef" :model="metaForm" :rules="rules" label-position="top">
          <div class="meta-grid">
            <el-form-item label="简历标题" prop="title">
              <el-input v-model="metaForm.title" placeholder="例如：林泽宇 - 后端开发工程师" />
            </el-form-item>
            <el-form-item label="默认简历">
              <el-switch v-model="metaForm.is_default" />
            </el-form-item>
          </div>
        </el-form>

        <ResumeFormEditor v-model:active-tab="activeTab" :form-api="formApi" />

        <div class="form-actions">
          <el-button @click="router.push({ name: 'resume-list' })">取消</el-button>
          <el-button type="primary" :loading="saving" @click="save">保存简历</el-button>
        </div>
      </section>

      <section class="panel">
        <div class="panel-title">
          <h2>实时预览</h2>
          <el-tag type="info">{{ currentTemplate.name }}</el-tag>
        </div>
        <div class="preview-shell">
          <ResumeStyledPreview
            ref="previewComponent"
            :snapshot="previewSnapshot"
            :template-id="templateId"
            :custom-template-content="customTemplateContent"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { resumeApi, templateApi } from "@/api/modules";
import type { ResumeTemplate } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import ResumeExportToolbar from "@/components/ResumeExportToolbar.vue";
import ResumeFormEditor from "@/components/ResumeFormEditor.vue";
import ResumeStyledPreview from "@/components/ResumeStyledPreview.vue";
import { getResumeTemplateId, useResumeForm } from "@/composables/useResumeForm";
import { buildExportFilename } from "@/utils/resumeExport";
import { snapshotFromPlainText } from "@/utils/resumeHelpers";
import {
  DEFAULT_RESUME_TEMPLATE_ID,
  filterSelectableCustomTemplates,
  findCustomTemplateContent,
  getCustomTemplateLabel,
  parseResumeTemplateQuery,
  type ResumeTemplateId
} from "@/utils/resumeTemplates";

const router = useRouter();
const route = useRoute();
const metaFormRef = ref<FormInstance>();
const activeTab = ref("basic");
const saving = ref(false);
const isEdit = computed(() => Boolean(route.params.id));
const templateId = ref<ResumeTemplateId>(DEFAULT_RESUME_TEMPLATE_ID);
const customTemplates = ref<ResumeTemplate[]>([]);
const previewComponent = ref<InstanceType<typeof ResumeStyledPreview>>();

const formApi = useResumeForm();
const { importSnapshot, packStoredContent, unpackStoredContent, exportSnapshot } = formApi;

const metaForm = reactive({
  title: "",
  file_url: null as string | null,
  is_default: false
});

const rules: FormRules<typeof metaForm> = {
  title: [{ required: true, message: "请输入简历标题", trigger: "blur" }]
};

const previewSnapshot = computed(() => exportSnapshot());
const customTemplateContent = computed(() => findCustomTemplateContent(customTemplates.value, templateId.value));
const currentTemplate = computed(() => ({
  name: getCustomTemplateLabel(customTemplates.value, templateId.value)
}));
const exportFilename = computed(() => buildExportFilename(previewSnapshot.value));

function loadContentToForm(content: string) {
  const { displayContent, snapshot } = unpackStoredContent(content);
  if (snapshot) {
    importSnapshot(snapshot);
    templateId.value = snapshot.templateId || getResumeTemplateId(content);
    return;
  }

  importSnapshot(snapshotFromPlainText(displayContent || content));
  templateId.value = DEFAULT_RESUME_TEMPLATE_ID;
}

async function save() {
  await metaFormRef.value?.validate();
  saving.value = true;
  try {
    const payload = {
      title: metaForm.title,
      content: packStoredContent(templateId.value),
      file_url: metaForm.file_url,
      is_default: metaForm.is_default
    };

    if (isEdit.value) {
      await resumeApi.update(Number(route.params.id), payload);
    } else {
      await resumeApi.create(payload);
    }
    ElMessage.success("简历已保存");
    router.push({ name: "resume-list" });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  try {
    customTemplates.value = filterSelectableCustomTemplates(await templateApi.list());
  } catch {
    customTemplates.value = [];
  }

  if (!isEdit.value) {
    formApi.resetForm();
    templateId.value = parseResumeTemplateQuery(route.query.template) ?? DEFAULT_RESUME_TEMPLATE_ID;
    const initialTemplateName = getCustomTemplateLabel(customTemplates.value, templateId.value);
    if (initialTemplateName && initialTemplateName !== "用户模板") {
      metaForm.title = `${initialTemplateName} 简历`;
    }
    return;
  }

  try {
    const resume = await resumeApi.get(Number(route.params.id));
    metaForm.title = resume.title;
    metaForm.file_url = resume.file_url;
    metaForm.is_default = resume.is_default;
    loadContentToForm(resume.content);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "简历加载失败");
  }
});
</script>

<style scoped>
.meta-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px;
  gap: 14px;
  align-items: end;
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

@media (max-width: 760px) {
  .meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
