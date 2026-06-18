<template>
  <div>
    <PageHeader
      title="首页仪表盘"
      description="集中查看简历、岗位、投递和面试进展，快速进入常用工作流。"
      eyebrow="JobPilot"
    >
      <template #actions>
        <el-button type="primary" :icon="EditPen" @click="router.push({ name: 'resume-new' })">新建简历</el-button>
        <el-button :icon="Briefcase" @click="router.push({ name: 'job-new' })">新增岗位</el-button>
      </template>
    </PageHeader>

    <div class="metric-grid">
      <MetricCard label="简历数量" :value="metrics.resumeCount" hint="含默认版本" tone="green">
        <template #icon><el-icon><Files /></el-icon></template>
      </MetricCard>
      <MetricCard label="活跃岗位" :value="metrics.activeJobCount" hint="招聘中岗位" tone="blue">
        <template #icon><el-icon><Briefcase /></el-icon></template>
      </MetricCard>
      <MetricCard label="投递记录" :value="metrics.applicationCount" hint="全状态汇总" tone="amber">
        <template #icon><el-icon><Promotion /></el-icon></template>
      </MetricCard>
      <MetricCard label="面试机会" :value="metrics.interviewCount" hint="笔试/面试/Offer" tone="rose">
        <template #icon><el-icon><Monitor /></el-icon></template>
      </MetricCard>
    </div>

    <div class="grid-2">
      <section class="panel">
        <div class="panel-title">
          <h2>最近简历</h2>
          <el-button link type="primary" @click="router.push({ name: 'resume-list' })">查看全部</el-button>
        </div>
        <el-skeleton v-if="loading" :rows="4" animated />
        <el-table v-else-if="resumes.length" :data="resumes.slice(0, 5)" size="large">
          <el-table-column prop="title" label="标题" min-width="160" />
          <el-table-column label="默认" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.is_default" type="success">默认</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click="router.push({ name: 'resume-edit', params: { id: row.id } })">
                编辑
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <EmptyState v-else description="还没有简历">
          <el-button type="primary" @click="router.push({ name: 'resume-new' })">新建简历</el-button>
        </EmptyState>
      </section>

      <section class="panel">
        <div class="panel-title">
          <h2>最近岗位</h2>
          <el-button link type="primary" @click="router.push({ name: 'job-list' })">查看全部</el-button>
        </div>
        <el-skeleton v-if="loading" :rows="4" animated />
        <el-table v-else-if="jobs.length" :data="jobs.slice(0, 5)" size="large">
          <el-table-column prop="title" label="岗位" min-width="150" />
          <el-table-column prop="company" label="公司" min-width="130" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag>{{ jobStatusLabels[row.status as JobStatus] || row.status }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
        <EmptyState v-else description="还没有岗位">
          <el-button type="primary" @click="router.push({ name: 'job-new' })">新增岗位</el-button>
        </EmptyState>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Briefcase, EditPen, Files, Monitor, Promotion } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { applicationApi, jobApi, resumeApi } from "@/api/modules";
import type { Application, Job, JobStatus, Resume } from "@/api/types";
import EmptyState from "@/components/EmptyState.vue";
import MetricCard from "@/components/MetricCard.vue";
import PageHeader from "@/components/PageHeader.vue";
import { buildDashboardMetrics } from "@/utils/statistics";
import { jobStatusLabels } from "@/utils/status";

const router = useRouter();
const loading = ref(true);
const resumes = ref<Resume[]>([]);
const jobs = ref<Job[]>([]);
const applications = ref<Application[]>([]);

const metrics = computed(() => buildDashboardMetrics(resumes.value, jobs.value, applications.value));

onMounted(async () => {
  try {
    const [resumeData, jobData, applicationData] = await Promise.all([
      resumeApi.list(),
      jobApi.list(),
      applicationApi.list()
    ]);
    resumes.value = resumeData;
    jobs.value = jobData;
    applications.value = applicationData;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "仪表盘数据加载失败");
  } finally {
    loading.value = false;
  }
});
</script>
