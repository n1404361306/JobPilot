<template>
  <div>
    <PageHeader title="岗位导入" description="支持文本、批量文本、URL、文件和截图导入，AI 解析后填入可编辑岗位表单。">
      <template #actions>
        <el-button :icon="Check" :loading="saving" @click="saveJob">保存表单</el-button>
        <el-button type="primary" :loading="importing" @click="importCurrent">导入当前来源</el-button>
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="文本" name="text">
            <el-input
              v-model="rawText"
              type="textarea"
              :rows="14"
              placeholder="粘贴岗位 JD、公司、地点、薪资、职责、要求、截止时间等文本。"
            />
          </el-tab-pane>

          <el-tab-pane label="批量文本" name="batch">
            <el-input
              v-model="batchText"
              type="textarea"
              :rows="14"
              placeholder="一次粘贴多个岗位。岗位之间可用空行、--- 或 ### 分隔；美团等平台列表会自动识别。"
            />
            <el-input v-model="batchSeparator" class="mt-12" placeholder="自定义分隔符，可不填" />
          </el-tab-pane>

          <el-tab-pane label="URL" name="url">
            <el-form label-position="top">
              <el-form-item label="岗位链接">
                <el-input v-model="urlText" placeholder="https://example.com/job/123" />
              </el-form-item>
              <el-form-item label="备用文本">
                <el-input
                  v-model="urlFallbackText"
                  type="textarea"
                  :rows="8"
                  placeholder="如果目标网站禁止抓取，可把页面文字粘贴到这里。"
                />
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="文件" name="file">
            <el-upload
              drag
              action="#"
              :auto-upload="false"
              accept=".pdf,.docx,.txt,.md"
              :limit="1"
              :show-file-list="false"
              :on-change="handleFileChange"
              :on-exceed="handleExceed"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">拖拽或点击上传岗位文件</div>
              <div class="el-upload__tip">支持 PDF、DOCX、TXT、MD</div>
            </el-upload>
            <div v-if="selectedFile" class="file-row">
              <span>{{ selectedFile.name }}</span>
              <el-button link type="danger" @click="selectedFile = null">移除</el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="截图" name="image">
            <el-upload
              drag
              action="#"
              :auto-upload="false"
              accept=".png,.jpg,.jpeg,.webp"
              :limit="1"
              :show-file-list="false"
              :on-change="handleImageChange"
              :on-exceed="handleExceed"
            >
              <el-icon class="el-icon--upload"><Picture /></el-icon>
              <div class="el-upload__text">拖拽或点击上传岗位截图</div>
              <div class="el-upload__tip">支持 PNG、JPG、JPEG、WEBP，使用本机 OCR 识别后再解析</div>
            </el-upload>
            <div v-if="selectedImage" class="file-row">
              <span>{{ selectedImage.name }}</span>
              <el-button link type="danger" @click="selectedImage = null">移除</el-button>
            </div>
          </el-tab-pane>
        </el-tabs>

        <el-alert
          class="source-tip"
          type="info"
          :closable="false"
          title="导入说明"
          description="系统优先用 AI 抽取岗位字段，失败时自动使用规则兜底。导入结果会填入右侧表单，可继续手动修改。"
        />

        <div v-if="batchDrafts.length" class="batch-result">
          <div class="panel-title">
            <h2>待确认岗位</h2>
            <div class="batch-actions">
              <el-tag type="warning">{{ batchDrafts.length }} 条待确认</el-tag>
              <el-button size="small" type="primary" :loading="confirmingBatch" @click="confirmBatchImport">确认批量导入</el-button>
            </div>
          </div>
          <el-alert
            class="mt-12"
            type="warning"
            :closable="false"
            title="请先检查解析结果。字段有误可以直接修改，确认后才会真正写入岗位库。"
          />
          <el-table :data="batchDrafts" size="small" class="mt-12">
            <el-table-column label="岗位" min-width="180">
              <template #default="{ row }">
                <el-input v-model="row.title" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="公司" min-width="160">
              <template #default="{ row }">
                <el-input v-model="row.company" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="地点" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.location" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="薪资" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.salary_range" size="small" />
              </template>
            </el-table-column>
            <el-table-column type="expand">
              <template #default="{ row }">
                <el-form class="batch-edit-form" label-position="top">
                  <div class="grid-2 compact-grid">
                    <el-form-item label="岗位类型">
                      <el-input v-model="row.job_type" />
                    </el-form-item>
                    <el-form-item label="截止时间">
                      <el-date-picker v-model="row.deadline" value-format="YYYY-MM-DD" type="date" style="width: 100%" />
                    </el-form-item>
                    <el-form-item label="来源链接">
                      <el-input v-model="row.source_url" />
                    </el-form-item>
                    <el-form-item label="标签">
                      <el-input v-model="row.tags" />
                    </el-form-item>
                  </div>
                  <el-form-item label="岗位描述">
                    <el-input v-model="row.description" type="textarea" :rows="6" />
                  </el-form-item>
                </el-form>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="110">
              <template #default="{ row, $index }">
                <el-button link type="primary" @click="fillDraft(row)">查看</el-button>
                <el-button link type="danger" @click="removeDraft($index)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>

      <section class="panel">
        <div class="panel-title">
          <h2>岗位表单</h2>
          <el-tag v-if="lastImportedId" type="success">已导入 #{{ lastImportedId }}</el-tag>
          <el-tag v-else type="info">可编辑</el-tag>
        </div>
        <el-form label-position="top">
          <div class="grid-2 compact-grid">
            <el-form-item label="岗位名称">
              <el-input v-model="form.title" />
            </el-form-item>
            <el-form-item label="公司">
              <el-input v-model="form.company" />
            </el-form-item>
            <el-form-item label="地点">
              <el-input v-model="form.location" />
            </el-form-item>
            <el-form-item label="薪资范围">
              <el-input v-model="form.salary_range" />
            </el-form-item>
            <el-form-item label="岗位类型">
              <el-input v-model="form.job_type" placeholder="后端开发 / 算法 / AI 应用" />
            </el-form-item>
            <el-form-item label="截止时间">
              <el-date-picker v-model="form.deadline" value-format="YYYY-MM-DD" type="date" style="width: 100%" />
            </el-form-item>
            <el-form-item label="来源类型">
              <el-input v-model="form.source_type" />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="招聘中" value="active" />
                <el-option label="已关闭" value="closed" />
                <el-option label="已归档" value="archived" />
              </el-select>
            </el-form-item>
          </div>
          <el-form-item label="来源链接">
            <el-input v-model="form.source_url" />
          </el-form-item>
          <el-form-item label="标签">
            <el-input v-model="form.tags" placeholder="多个标签用逗号分隔，如 Java,Spring Boot,AI" />
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="form.is_favorite">收藏岗位</el-checkbox>
          </el-form-item>
          <el-form-item label="岗位描述">
            <el-input v-model="form.description" type="textarea" :rows="10" />
          </el-form-item>
        </el-form>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check, Picture, UploadFilled } from "@element-plus/icons-vue";
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import { reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { jobApi } from "@/api/modules";
import type { Job, JobPayload, JobStatus } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const router = useRouter();
const activeTab = ref("text");
const rawText = ref("");
const batchText = ref("");
const batchSeparator = ref("");
const urlText = ref("");
const urlFallbackText = ref("");
const selectedFile = ref<File | null>(null);
const selectedImage = ref<File | null>(null);
const saving = ref(false);
const importing = ref(false);
const confirmingBatch = ref(false);
const lastImportedId = ref<number | null>(null);
const batchDrafts = ref<JobPayload[]>([]);

const form = reactive({
  title: "",
  company: "",
  location: "",
  salary_range: "",
  source_url: "",
  source_type: "manual",
  job_type: "",
  deadline: "",
  tags: "",
  is_favorite: false,
  description: "",
  status: "active" as JobStatus
});

watch(rawText, (value) => {
  if (!form.description) {
    form.description = value;
  }
});

function fillJob(job: Job) {
  Object.assign(form, {
    title: job.title,
    company: job.company,
    location: job.location || "",
    salary_range: job.salary_range || "",
    source_url: job.source_url || "",
    source_type: job.source_type || "",
    job_type: job.job_type || "",
    deadline: job.deadline || "",
    tags: job.tags || "",
    is_favorite: Boolean(job.is_favorite),
    description: job.description || "",
    status: (job.status || "active") as JobStatus
  });
  lastImportedId.value = job.id;
}

function fillDraft(job: JobPayload) {
  Object.assign(form, {
    title: job.title,
    company: job.company,
    location: job.location || "",
    salary_range: job.salary_range || "",
    source_url: job.source_url || "",
    source_type: job.source_type || "batch_text",
    job_type: job.job_type || "",
    deadline: job.deadline || "",
    tags: job.tags || "",
    is_favorite: Boolean(job.is_favorite),
    description: job.description || "",
    status: (job.status || "active") as JobStatus
  });
  lastImportedId.value = null;
}

function removeDraft(index: number) {
  batchDrafts.value.splice(index, 1);
}

function handleFileChange(file: UploadFile) {
  selectedFile.value = file.raw || null;
}

function handleImageChange(file: UploadFile) {
  selectedImage.value = file.raw || null;
}

function handleExceed() {
  ElMessage.warning("一次只能上传一个文件，请先移除当前文件");
}

function buildPayload() {
  return {
    title: form.title,
    company: form.company,
    location: form.location || null,
    salary_range: form.salary_range || null,
    source_url: form.source_url || null,
    source_type: form.source_type || null,
    job_type: form.job_type || null,
    deadline: form.deadline || null,
    tags: form.tags || null,
    is_favorite: form.is_favorite,
    description: form.description || null,
    status: form.status
  };
}

async function saveJob() {
  if (!form.title || !form.company) {
    ElMessage.warning("请填写岗位名称和公司");
    return;
  }

  saving.value = true;
  try {
    const job = await jobApi.create(buildPayload());
    ElMessage.success("岗位已保存");
    router.push({ name: "job-detail", params: { id: job.id } });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

function normalizeBatchDraft(job: JobPayload): JobPayload {
  return {
    title: job.title.trim(),
    company: job.company.trim(),
    location: job.location || null,
    salary_range: job.salary_range || null,
    source_url: job.source_url || null,
    source_type: "batch_text",
    job_type: job.job_type || null,
    deadline: job.deadline || null,
    tags: job.tags || null,
    is_favorite: Boolean(job.is_favorite),
    import_batch_id: null,
    description: job.description || null,
    status: (job.status || "active") as JobStatus
  };
}

async function confirmBatchImport() {
  if (!batchDrafts.value.length) {
    ElMessage.warning("请先解析批量岗位文本");
    return;
  }
  const invalidIndex = batchDrafts.value.findIndex((job) => !job.title?.trim() || !job.company?.trim());
  if (invalidIndex >= 0) {
    ElMessage.warning(`第 ${invalidIndex + 1} 条岗位缺少岗位名称或公司`);
    return;
  }

  confirmingBatch.value = true;
  try {
    const result = await jobApi.importBatchText({
      jobs: batchDrafts.value.map(normalizeBatchDraft)
    });
    batchDrafts.value = [];
    ElMessage.success(`已确认导入 ${result.count} 条岗位`);
    router.push({ name: "job-list" });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "确认批量导入失败");
  } finally {
    confirmingBatch.value = false;
  }
}

async function importCurrent() {
  importing.value = true;
  try {
    let job: Job;
    if (activeTab.value === "text") {
      if (!rawText.value.trim()) {
        ElMessage.warning("请先粘贴岗位文本");
        return;
      }
      job = await jobApi.importText({ text: rawText.value, source_url: form.source_url || null });
    } else if (activeTab.value === "batch") {
      if (!batchText.value.trim()) {
        ElMessage.warning("请先粘贴批量岗位文本");
        return;
      }
      batchDrafts.value = (
        await jobApi.previewBatchText({
          text: batchText.value,
          separator: batchSeparator.value.trim() || null
        })
      ).jobs;
      if (batchDrafts.value.length) {
        fillDraft(batchDrafts.value[0]);
      }
      ElMessage.success(`已解析 ${batchDrafts.value.length} 条岗位，请确认后导入`);
      return;
    } else if (activeTab.value === "url") {
      if (!urlText.value.trim()) {
        ElMessage.warning("请先填写岗位链接");
        return;
      }
      job = await jobApi.importUrl({
        source_url: urlText.value,
        text: urlFallbackText.value.trim() || null
      });
    } else if (activeTab.value === "file") {
      if (!selectedFile.value) {
        ElMessage.warning("请先上传岗位文件");
        return;
      }
      job = await jobApi.importFile(selectedFile.value);
    } else {
      if (!selectedImage.value) {
        ElMessage.warning("请先上传岗位截图");
        return;
      }
      job = await jobApi.importImage(selectedImage.value);
    }

    fillJob(job);
    ElMessage.success("岗位已导入");
    router.push({ name: "job-detail", params: { id: job.id } });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "导入失败");
  } finally {
    importing.value = false;
  }
}
</script>

<style scoped>
.source-tip,
.batch-result,
.mt-12 {
  margin-top: 12px;
}

.compact-grid {
  align-items: start;
}

.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: #f8fafc;
}

.file-row span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
