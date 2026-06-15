<template>
  <div>
    <PageHeader title="数据统计" description="基于真实简历、岗位和投递记录生成统计图表，手机端纵向排列。" />

    <div class="metric-grid">
      <MetricCard label="简历" :value="metrics.resumeCount" hint="版本数量" tone="green" />
      <MetricCard label="岗位" :value="jobs.length" hint="岗位库" tone="blue" />
      <MetricCard label="投递" :value="metrics.applicationCount" hint="投递记录" tone="amber" />
      <MetricCard label="Offer" :value="metrics.offerCount" hint="成功机会" tone="rose" />
    </div>

    <div class="grid-2">
      <section class="panel">
        <div class="panel-title">
          <h2>投递状态分布</h2>
        </div>
        <div ref="statusChartRef" class="chart-box"></div>
      </section>
      <section class="panel">
        <div class="panel-title">
          <h2>渠道分布</h2>
        </div>
        <div ref="channelChartRef" class="chart-box"></div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { ElMessage } from "element-plus";
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { applicationApi, jobApi, resumeApi } from "@/api/modules";
import type { Application, Job, Resume } from "@/api/types";
import MetricCard from "@/components/MetricCard.vue";
import PageHeader from "@/components/PageHeader.vue";
import { buildApplicationSummary, buildChannelSummary, buildDashboardMetrics } from "@/utils/statistics";
import { applicationStatusLabels, applicationStatusOrder } from "@/utils/status";

const resumes = ref<Resume[]>([]);
const jobs = ref<Job[]>([]);
const applications = ref<Application[]>([]);
const statusChartRef = ref<HTMLDivElement>();
const channelChartRef = ref<HTMLDivElement>();
let statusChart: echarts.ECharts | null = null;
let channelChart: echarts.ECharts | null = null;

const metrics = computed(() => buildDashboardMetrics(resumes.value, jobs.value, applications.value));

async function load() {
  try {
    const [resumeData, jobData, applicationData] = await Promise.all([
      resumeApi.list(),
      jobApi.list(),
      applicationApi.list()
    ]);
    resumes.value = resumeData;
    jobs.value = jobData;
    applications.value = applicationData;
    await nextTick();
    renderCharts();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "统计数据加载失败");
  }
}

function renderCharts() {
  const summary = buildApplicationSummary(applications.value);
  const channelSummary = buildChannelSummary(applications.value);

  if (statusChartRef.value) {
    statusChart = echarts.init(statusChartRef.value);
    statusChart.setOption({
      tooltip: {},
      xAxis: { type: "category", data: applicationStatusOrder.map((status) => applicationStatusLabels[status]) },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: applicationStatusOrder.map((status) => summary[status]), color: "#0f766e" }]
    });
  }

  if (channelChartRef.value) {
    channelChart = echarts.init(channelChartRef.value);
    channelChart.setOption({
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["45%", "72%"],
          data: channelSummary.length ? channelSummary : [{ name: "暂无数据", value: 1 }],
          color: ["#2563eb", "#0f766e", "#b45309", "#be123c", "#64748b"]
        }
      ]
    });
  }
}

function resizeCharts() {
  statusChart?.resize();
  channelChart?.resize();
}

onMounted(() => {
  load();
  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  statusChart?.dispose();
  channelChart?.dispose();
});
</script>
