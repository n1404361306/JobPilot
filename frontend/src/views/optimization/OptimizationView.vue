<template>
  <div>
    <PageHeader title="简历优化和岗位适配" description="针对目标岗位生成优化建议与适配版本。">
      <template #actions>
        <el-button type="primary" :loading="loading" @click="run">生成建议</el-button>
        <el-button :loading="draftLoading" @click="generateDraft">生成新版简历</el-button>
        <el-button type="success" :disabled="!draftContent" :loading="savingDraft" @click="saveAsResume">另存为新简历</el-button>
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <el-form label-position="top">
          <el-form-item label="简历">
            <el-select v-model="form.resume_id" placeholder="选择简历" class="full">
              <el-option v-for="resume in resumes" :key="resume.id" :label="resume.title" :value="resume.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="岗位">
            <el-select v-model="form.job_id" clearable placeholder="可选：选择目标岗位" class="full">
              <el-option v-for="job in jobs" :key="job.id" :label="`${job.company} - ${job.title}`" :value="job.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="补充要求">
            <el-input v-model="extra" type="textarea" :rows="6" placeholder="例如：突出 Java 后端、数据库优化、团队协作" />
          </el-form-item>
          <el-form-item label="新简历保存标题">
            <el-input v-model="draftTitle" placeholder="例如：后端开发岗位适配版简历" />
          </el-form-item>
        </el-form>
      </section>

      <section class="panel">
        <el-tabs>
          <el-tab-pane label="优化建议">
            <el-empty v-if="!optimize" description="暂无优化建议" />
            <pre v-else class="text-output">{{ displayText(optimize) }}</pre>
          </el-tab-pane>
          <el-tab-pane label="岗位适配">
            <el-empty v-if="!adapt" description="暂无适配建议" />
            <pre v-else class="text-output">{{ displayText(adapt) }}</pre>
          </el-tab-pane>
          <el-tab-pane label="新版简历">
            <el-empty v-if="!draftReady" description="可点击「生成新版简历」按要求生成适配版简历" />
            <ResumeFormEditor v-else v-model:active-tab="draftActiveTab" :form-api="generatedForm" />
          </el-tab-pane>
        </el-tabs>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { aiApi, jobApi, resumeApi } from "@/api/modules";
import type { AIResult, Job, Resume } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import ResumeFormEditor from "@/components/ResumeFormEditor.vue";
import {
  getResumeDisplayContent,
  getResumeSnapshot,
  getResumeTemplateId,
  useResumeForm,
  type ResumeFormSnapshot
} from "@/composables/useResumeForm";
import { snapshotFromPlainText } from "@/utils/resumeHelpers";
import { DEFAULT_RESUME_TEMPLATE_ID, type ResumeTemplateId } from "@/utils/resumeTemplates";
import { stripMarkdown } from "@/utils/textFormat";

function displayText(result: AIResult | null) {
  return result ? stripMarkdown(result.content) : "";
}

const resumes = ref<Resume[]>([]);
const jobs = ref<Job[]>([]);
const optimize = ref<AIResult | null>(null);
const adapt = ref<AIResult | null>(null);
const loading = ref(false);
const draftLoading = ref(false);
const savingDraft = ref(false);
const draftReady = ref(false);
const draftTitle = ref("");
const draftActiveTab = ref("basic");
const draftTemplateId = ref<ResumeTemplateId>(DEFAULT_RESUME_TEMPLATE_ID);
const extra = ref("");
const form = reactive<{ resume_id?: number; job_id?: number }>({});
const generatedForm = useResumeForm();
const { importSnapshot, packStoredContent } = generatedForm;
const draftContent = computed(() => (draftReady.value ? generatedForm.resumeContent.value : ""));

const selectedResume = computed(() => resumes.value.find((item) => item.id === form.resume_id));
const selectedJob = computed(() => jobs.value.find((item) => item.id === form.job_id));

onMounted(async () => {
  [resumes.value, jobs.value] = await Promise.all([resumeApi.list(), jobApi.list()]);
});

watch(
  () => [form.resume_id, form.job_id],
  () => {
    const resume = selectedResume.value;
    const job = selectedJob.value;
    if (resume && !draftTitle.value) {
      draftTitle.value = job ? `${resume.title} - ${job.title}适配版` : `${resume.title} - 优化版`;
    }
  }
);

function ensureSelection() {
  if (!form.resume_id) {
    ElMessage.warning("请选择简历");
    return false;
  }
  return true;
}

function buildContext() {
  const resume = selectedResume.value;
  const job = selectedJob.value;
  return [
    "原始简历：",
    resume ? getResumeDisplayContent(resume.content) : "",
    "",
    "目标岗位：",
    job ? `${job.company} - ${job.title}` : "未选择具体岗位，按用户补充要求进行通用优化",
    job?.description || "",
    "",
    "用户补充要求：",
    extra.value || "无"
  ].join("\n");
}

async function run() {
  if (!ensureSelection()) return;
  const text = buildContext();
  loading.value = true;
  try {
    [optimize.value, adapt.value] = await Promise.all([
      aiApi.optimizeResume(text, form.resume_id, form.job_id),
      aiApi.adaptResume(text, form.resume_id, form.job_id)
    ]);
    ElMessage.success("建议已生成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "生成失败");
  } finally {
    loading.value = false;
  }
}

async function generateDraft() {
  if (!ensureSelection()) return;
  draftLoading.value = true;
  try {
    const instruction = [
      buildContext(),
      "",
      "请根据上面的原始简历、目标岗位和用户补充要求，直接生成一份完整的新简历正文。",
      "要求：",
      "1. 保留用户真实经历，不要编造学校、公司、项目、证书、奖项或数据。",
      "2. 可以重组表达、调整顺序、强化与目标岗位相关的关键词。",
      "3. 如果信息缺失，用“待补充”标注，不要虚构。",
      "4. 只输出可直接保存为简历的正文，不要输出优化建议、解释或 Markdown 标记。"
    ].join("\n");
    const result = await aiApi.adaptResume(instruction, form.resume_id, form.job_id);
    const generatedContent = stripMarkdown(result.content).trim();
    const snapshot = await buildDraftSnapshot(generatedContent);
    importSnapshot(snapshot);
    draftReady.value = true;
    draftActiveTab.value = "basic";
    if (!draftTitle.value && selectedResume.value) {
      draftTitle.value = selectedJob.value
        ? `${selectedResume.value.title} - ${selectedJob.value.title}适配版`
        : `${selectedResume.value.title} - 优化版`;
    }
    ElMessage.success("新版简历已生成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "新版简历生成失败");
  } finally {
    draftLoading.value = false;
  }
}

function sourceSnapshot() {
  return selectedResume.value ? getResumeSnapshot(selectedResume.value.content) : null;
}

function applySourceFormMeta(snapshot: ResumeFormSnapshot) {
  const source = sourceSnapshot();
  if (source?.basic_info.photo) {
    snapshot.basic_info.photo = source.basic_info.photo;
  }
  if (selectedResume.value) {
    draftTemplateId.value = getResumeTemplateId(selectedResume.value.content);
    snapshot.templateId = draftTemplateId.value;
  }
  return snapshot;
}

async function buildDraftSnapshot(content: string) {
  const fallback = applySourceFormMeta(snapshotFromPlainText(content));
  try {
    const parsed = await aiApi.parseResume(content);
    generatedForm.resetForm();
    generatedForm.fillForm(parsed.data || {});
    return applySourceFormMeta(generatedForm.exportSnapshot());
  } catch {
    ElMessage.warning("新版简历已生成，但结构化解析失败，将按正文保存为可编辑表单");
    return fallback;
  }
}

async function saveAsResume() {
  if (!draftContent.value.trim()) {
    ElMessage.warning("请先生成新版简历");
    return;
  }
  savingDraft.value = true;
  try {
    const resume = await resumeApi.create({
      title: draftTitle.value.trim() || "岗位适配版简历",
      content: packStoredContent(draftTemplateId.value),
      is_default: false
    });
    resumes.value = await resumeApi.list();
    ElMessage.success("已另存为新简历");
    form.resume_id = resume.id;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "另存失败");
  } finally {
    savingDraft.value = false;
  }
}
</script>

<style scoped>
.full {
  width: 100%;
}

.text-output {
  white-space: pre-wrap;
  line-height: 1.7;
  margin: 0;
}
</style>
