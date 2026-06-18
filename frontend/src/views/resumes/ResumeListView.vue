<template>
  <div>
    <PageHeader title="简历列表和版本管理" description="管理不同岗位方向的简历版本，并快速套用预设模板。">
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="router.push({ name: 'resume-new' })">新建简历</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <el-skeleton v-if="loading" :rows="5" animated />
      <template v-else-if="resumes.length">
      <div class="batch-toolbar">
        <span class="muted">已选择 {{ selectedResumes.length }} 份简历</span>
        <el-select v-model="batchTemplateId" class="template-select" placeholder="选择模板" filterable>
          <el-option-group label="内置模板">
            <el-option
              v-for="preset in RESUME_TEMPLATE_PRESETS"
              :key="preset.id"
              :label="preset.name"
              :value="preset.id"
            />
          </el-option-group>
          <el-option-group v-if="customTemplates.length" label="用户模板">
            <el-option
              v-for="template in customTemplates"
              :key="template.id"
              :label="`${template.name}（${template.is_public ? '公开' : '私有'}）`"
              :value="customTemplateId(template.id)"
            />
          </el-option-group>
        </el-select>
        <el-button
          type="primary"
          :disabled="!selectedResumes.length"
          :loading="applyingTemplate"
          @click="applyTemplateToSelected"
        >
          批量套模板
        </el-button>
        <el-button
          type="danger"
          :disabled="!selectedResumes.length"
          :loading="bulkDeleting"
          @click="removeSelected"
        >
          批量删除
        </el-button>
      </div>
      <el-table
        :data="resumes"
        row-key="id"
        size="large"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="title" label="简历标题" min-width="180" />
        <el-table-column label="当前模板" width="130">
          <template #default="{ row }">
            <el-tag effect="plain" :style="templateTagStyle(row)">{{ templateName(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="默认版本" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success">默认</el-tag>
            <el-button v-else link type="primary" @click="setDefault(row)">设为默认</el-button>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openTemplateDialog(row)">套模板</el-button>
            <el-button link type="primary" @click="router.push({ name: 'resume-edit', params: { id: row.id } })">编辑</el-button>
            <el-button link type="primary" @click="goPreview(row)">预览</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      </template>
      <EmptyState v-else description="暂无简历版本">
        <el-button type="primary" @click="router.push({ name: 'resume-new' })">创建第一份简历</el-button>
      </EmptyState>
    </section>

    <ResumeTemplateDialog
      v-model:visible="templateDialogVisible"
      :resume="activeResume"
      @applied="load"
    />
  </div>
</template>

<script setup lang="ts">
import { Plus } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { resumeApi, templateApi } from "@/api/modules";
import type { Resume, ResumeTemplate } from "@/api/types";
import EmptyState from "@/components/EmptyState.vue";
import PageHeader from "@/components/PageHeader.vue";
import ResumeTemplateDialog from "@/components/ResumeTemplateDialog.vue";
import { getResumeTemplateId } from "@/composables/useResumeForm";
import { formatDateTime } from "@/utils/status";
import {
  customTemplateId,
  DEFAULT_RESUME_TEMPLATE_ID,
  filterSelectableCustomTemplates,
  getCustomTemplateLabel,
  getTemplatePreset,
  parseCustomTemplateId,
  RESUME_TEMPLATE_PRESETS,
  type ResumeTemplateId
} from "@/utils/resumeTemplates";

const router = useRouter();
const loading = ref(true);
const bulkDeleting = ref(false);
const applyingTemplate = ref(false);
const resumes = ref<Resume[]>([]);
const customTemplates = ref<ResumeTemplate[]>([]);
const selectedResumes = ref<Resume[]>([]);
const batchTemplateId = ref<ResumeTemplateId>(DEFAULT_RESUME_TEMPLATE_ID);
const templateDialogVisible = ref(false);
const activeResume = ref<Resume | null>(null);

function templateName(resume: Resume) {
  const id = getResumeTemplateId(resume.content);
  return getCustomTemplateLabel(customTemplates.value, id);
}

function templateTagStyle(resume: Resume) {
  const id = getResumeTemplateId(resume.content);
  const customId = parseCustomTemplateId(id);
  if (customId) {
    return {
      color: "#b45309",
      borderColor: "#f59e0b55",
      background: "#f59e0b10"
    };
  }
  const preset = getTemplatePreset(id);
  return {
    color: preset.accent,
    borderColor: `${preset.accent}55`,
    background: `${preset.accent}10`
  };
}

function openTemplateDialog(resume: Resume) {
  activeResume.value = resume;
  templateDialogVisible.value = true;
}

function goPreview(resume: Resume) {
  router.push({
    name: "resume-preview",
    params: { id: resume.id }
  });
}

async function load() {
  loading.value = true;
  try {
    const [resumeList, templateList] = await Promise.all([resumeApi.list(), templateApi.list()]);
    resumes.value = resumeList;
    customTemplates.value = filterSelectableCustomTemplates(templateList);
    selectedResumes.value = [];
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "简历加载失败");
  } finally {
    loading.value = false;
  }
}

function handleSelectionChange(selection: Resume[]) {
  selectedResumes.value = selection;
}

async function setDefault(resume: Resume) {
  await resumeApi.update(resume.id, { is_default: true });
  ElMessage.success("已设置默认简历");
  await load();
}

async function remove(resume: Resume) {
  await ElMessageBox.confirm(`确认删除「${resume.title}」？`, "删除简历", { type: "warning" });
  await resumeApi.remove(resume.id);
  ElMessage.success("已删除");
  await load();
}

async function removeSelected() {
  if (!selectedResumes.value.length) return;
  await ElMessageBox.confirm(`确认删除选中的 ${selectedResumes.value.length} 份简历？`, "批量删除简历", { type: "warning" });
  bulkDeleting.value = true;
  try {
    for (const resume of selectedResumes.value) {
      await resumeApi.remove(resume.id);
    }
    ElMessage.success("已批量删除简历");
    await load();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "批量删除失败");
  } finally {
    bulkDeleting.value = false;
  }
}

async function applyTemplateToSelected() {
  if (!selectedResumes.value.length) return;
  applyingTemplate.value = true;
  try {
    for (const resume of selectedResumes.value) {
      await resumeApi.selectTemplate(resume.id, batchTemplateId.value);
    }
    ElMessage.success("已批量套用模板");
    await load();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "批量套模板失败");
  } finally {
    applyingTemplate.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.batch-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 12px;
}

.template-select {
  width: 240px;
}

.muted {
  color: #8a94a6;
  font-size: 13px;
}
</style>
