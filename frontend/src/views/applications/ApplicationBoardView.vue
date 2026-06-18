<template>
  <div>
    <PageHeader title="投递看板" description="按文档状态机管理投递进展，覆盖筛选、笔试、多轮面试、Offer、拒绝和放弃。">
      <template #actions>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </template>
    </PageHeader>

    <section class="kanban-board">
      <article v-for="status in applicationStatusOrder" :key="status" class="kanban-column">
        <div class="panel-title">
          <h2>{{ applicationStatusLabels[status] }}</h2>
          <el-tag :type="applicationStatusTypes[status]">{{ grouped[status].length }}</el-tag>
        </div>
        <div v-if="grouped[status].length">
          <div v-for="application in grouped[status]" :key="application.id" class="kanban-card">
            <strong>{{ jobMap.get(application.job_id)?.title || `岗位 #${application.job_id}` }}</strong>
            <p>{{ jobMap.get(application.job_id)?.company || "公司未记录" }}</p>
            <p>渠道：{{ application.channel || "未记录" }}</p>
            <p>投递：{{ formatDateTime(application.applied_at) }}</p>
            <p v-if="application.note">备注：{{ application.note }}</p>
            <el-select
              :model-value="application.status"
              size="small"
              style="width: 100%; margin-top: 8px"
              @change="handleStatusChange(application, $event)"
            >
              <el-option
                v-for="option in applicationStatusOrder"
                :key="option"
                :label="applicationStatusLabels[option]"
                :value="option"
              />
            </el-select>
          </div>
        </div>
        <p v-else class="muted">暂无记录</p>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { applicationApi, jobApi } from "@/api/modules";
import type { Application, ApplicationStatus, Job } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import {
  applicationStatusLabels,
  applicationStatusOrder,
  applicationStatusTypes,
  formatDateTime
} from "@/utils/status";

const applications = ref<Application[]>([]);
const jobs = ref<Job[]>([]);
const jobMap = computed(() => new Map(jobs.value.map((job) => [job.id, job])));

const grouped = computed(() => {
  const result = applicationStatusOrder.reduce(
    (acc, status) => {
      acc[status] = [];
      return acc;
    },
    {} as Record<ApplicationStatus, Application[]>
  );

  for (const application of applications.value) {
    const status = applicationStatusOrder.includes(application.status as ApplicationStatus)
      ? (application.status as ApplicationStatus)
      : "pending";
    result[status].push(application);
  }

  return result;
});

async function load() {
  try {
    const [applicationData, jobData] = await Promise.all([applicationApi.list(), jobApi.list()]);
    applications.value = applicationData;
    jobs.value = jobData;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "投递看板加载失败");
  }
}

function handleStatusChange(application: Application, value: string | number | boolean) {
  updateStatus(application, value as ApplicationStatus);
}

async function updateStatus(application: Application, status: ApplicationStatus) {
  await applicationApi.updateStatus(application.id, { status });
  ElMessage.success("状态已更新");
  await load();
}

onMounted(load);
</script>

<style scoped>
.muted {
  color: #8a94a6;
  font-size: 13px;
}

.kanban-card p {
  margin: 6px 0 0;
  color: #667085;
  font-size: 13px;
}
</style>
