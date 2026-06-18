<template>
  <div>
    <PageHeader title="岗位列表" description="管理岗位库，支持按状态和关键词筛选，展示来源、标签、截止时间等结构化字段。">
      <template #actions>
        <el-button :icon="Upload" @click="router.push({ name: 'job-import' })">导入岗位</el-button>
        <el-button type="primary" :icon="Plus" @click="router.push({ name: 'job-new' })">新增岗位</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <el-form class="filter-bar" inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" clearable placeholder="岗位或公司" @keyup.enter="load" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
            <el-option label="招聘中" value="active" />
            <el-option label="已关闭" value="closed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">筛选</el-button>
        </el-form-item>
      </el-form>

      <div class="batch-toolbar">
        <span class="muted">已选择 {{ selectedJobs.length }} 个岗位</span>
        <el-button
          type="danger"
          :disabled="!selectedJobs.length"
          :loading="bulkDeleting"
          @click="removeSelected"
        >
          批量删除
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="jobs"
        row-key="id"
        size="large"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="title" label="岗位" min-width="160" />
        <el-table-column prop="company" label="公司" min-width="140" />
        <el-table-column prop="location" label="地点" min-width="110" />
        <el-table-column prop="job_type" label="类型" min-width="120" />
        <el-table-column prop="salary_range" label="薪资" min-width="120" />
        <el-table-column prop="deadline" label="截止时间" min-width="120" />
        <el-table-column label="标签" min-width="160">
          <template #default="{ row }">
            <el-tag v-for="tag in splitTags(row.tags)" :key="tag" class="tag-item" size="small">{{ tag }}</el-tag>
            <span v-if="!splitTags(row.tags).length" class="muted">未记录</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag>{{ jobStatusLabels[row.status as JobStatus] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="投递状态" min-width="150">
          <template #default="{ row }">
            <el-select
              v-if="applicationByJob[row.id]"
              :model-value="applicationByJob[row.id].status"
              size="small"
              @change="updateApplicationStatus(row.id, $event)"
            >
              <el-option
                v-for="status in applicationStatusOrder"
                :key="status"
                :label="applicationStatusLabels[status]"
                :value="status"
              />
            </el-select>
            <el-tag v-else type="info" effect="plain">未加入投递</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push({ name: 'job-detail', params: { id: row.id } })">详情</el-button>
            <el-button link type="primary" @click="createApplication(row)">加入投递</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Plus, Upload } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { applicationApi, jobApi } from "@/api/modules";
import type { Application, ApplicationStatus, Job, JobStatus } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import { applicationStatusLabels, applicationStatusOrder, jobStatusLabels } from "@/utils/status";

const router = useRouter();
const loading = ref(false);
const bulkDeleting = ref(false);
const jobs = ref<Job[]>([]);
const applications = ref<Application[]>([]);
const selectedJobs = ref<Job[]>([]);
const filters = reactive({ keyword: "", status: "" });

const applicationByJob = computed<Record<number, Application>>(() => {
  const mapped: Record<number, Application> = {};
  for (const application of applications.value) {
    if (!mapped[application.job_id]) {
      mapped[application.job_id] = application;
    }
  }
  return mapped;
});

function splitTags(value: string | null | undefined) {
  return (value || "")
    .split(/[，,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

async function load() {
  loading.value = true;
  try {
    const [jobList, applicationList] = await Promise.all([
      jobApi.list({
        keyword: filters.keyword || undefined,
        status: filters.status || undefined
      }),
      applicationApi.list()
    ]);
    jobs.value = jobList;
    applications.value = applicationList;
    selectedJobs.value = [];
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "岗位加载失败");
  } finally {
    loading.value = false;
  }
}

function handleSelectionChange(selection: Job[]) {
  selectedJobs.value = selection;
}

async function createApplication(job: Job) {
  const existed = applicationByJob.value[job.id];
  if (existed) {
    ElMessage.info("该岗位已在投递看板中");
    return;
  }
  await applicationApi.create({ job_id: job.id, status: "pending", channel: "手动加入" });
  applications.value = await applicationApi.list();
  ElMessage.success("已加入投递看板");
}

async function updateApplicationStatus(jobId: number, status: string) {
  const application = applicationByJob.value[jobId];
  if (!application) return;
  try {
    const updated = await applicationApi.updateStatus(application.id, { status: status as ApplicationStatus });
    applications.value = applications.value.map((item) => (item.id === updated.id ? updated : item));
    ElMessage.success("投递状态已更新");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "投递状态更新失败");
  }
}

async function remove(job: Job) {
  await ElMessageBox.confirm(`确认删除「${job.title}」？`, "删除岗位", { type: "warning" });
  await jobApi.remove(job.id);
  ElMessage.success("已删除");
  await load();
}

async function removeSelected() {
  if (!selectedJobs.value.length) return;
  await ElMessageBox.confirm(`确认删除选中的 ${selectedJobs.value.length} 个岗位？`, "批量删除岗位", { type: "warning" });
  bulkDeleting.value = true;
  try {
    for (const job of selectedJobs.value) {
      await jobApi.remove(job.id);
    }
    ElMessage.success("已批量删除岗位");
    await load();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "批量删除失败");
  } finally {
    bulkDeleting.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.filter-bar {
  margin-bottom: 12px;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 12px;
}

.tag-item {
  margin: 2px 4px 2px 0;
}

.muted {
  color: #8a94a6;
  font-size: 13px;
}
</style>
