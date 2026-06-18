<template>
  <div>
    <PageHeader title="数据统计" description="展示投递、岗位、匹配报告和转化率等课程文档要求的统计指标。" />

    <div class="metric-grid">
      <MetricCard label="简历" :value="overview?.resume_count || 0" hint="简历数量" tone="green" />
      <MetricCard
        label="活跃岗位"
        :value="jobsStats?.active_count || overview?.active_job_count || 0"
        :hint="`全部岗位 ${jobsStats?.total || overview?.job_count || 0}`"
        tone="blue"
      />
      <MetricCard label="投递" :value="applicationsStats?.total || overview?.application_count || 0" hint="投递记录" tone="amber" />
      <MetricCard
        label="平均匹配"
        :value="`${Math.round(matchesStats?.average_score || overview?.average_match_score || 0)}分`"
        hint="匹配报告"
        tone="rose"
      />
    </div>

    <div class="metric-grid compact">
      <MetricCard
        label="面试转化"
        :value="formatPercentRate(applicationsStats?.interview_conversion_rate)"
        :hint="`进入笔试/面试/Offer ${applicationsStats?.interview_count || 0} 条`"
        tone="blue"
      />
      <MetricCard
        label="Offer 转化"
        :value="formatPercentRate(applicationsStats?.offer_conversion_rate)"
        :hint="`获得 Offer ${applicationsStats?.offer_count || 0} 条`"
        tone="green"
      />
      <MetricCard label="收藏岗位" :value="jobsStats?.favorite_count || 0" hint="岗位列表可收藏" tone="amber" />
      <MetricCard label="匹配报告" :value="matchesStats?.total || overview?.match_report_count || 0" hint="分析次数" tone="rose" />
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
          <h2>岗位来源分布</h2>
        </div>
        <div ref="sourceChartRef" class="chart-box"></div>
      </section>
      <section class="panel">
        <div class="panel-title">
          <h2>岗位类型</h2>
        </div>
        <div ref="typeChartRef" class="chart-box"></div>
      </section>
      <section class="panel">
        <div class="panel-title">
          <h2>匹配分数区间</h2>
        </div>
        <div ref="matchChartRef" class="chart-box"></div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { ElMessage } from "element-plus";
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { statisticsApi } from "@/api/modules";
import type { StatisticsApplications, StatisticsJobs, StatisticsMatches, StatisticsOverview } from "@/api/types";
import MetricCard from "@/components/MetricCard.vue";
import PageHeader from "@/components/PageHeader.vue";
import {
  formatPercentRate,
  labelJobSource,
  MATCH_SCORE_RANGE_ORDER,
  normalizeStatusCounts,
  sortEntriesByCount
} from "@/utils/statistics";
import { applicationStatusLabels, applicationStatusOrder } from "@/utils/status";

const overview = ref<StatisticsOverview | null>(null);
const applicationsStats = ref<StatisticsApplications | null>(null);
const jobsStats = ref<StatisticsJobs | null>(null);
const matchesStats = ref<StatisticsMatches | null>(null);

const statusChartRef = ref<HTMLDivElement>();
const sourceChartRef = ref<HTMLDivElement>();
const typeChartRef = ref<HTMLDivElement>();
const matchChartRef = ref<HTMLDivElement>();
let charts: echarts.ECharts[] = [];

async function load() {
  try {
    const [overviewData, applicationData, jobData, matchData] = await Promise.all([
      statisticsApi.overview(),
      statisticsApi.applications(),
      statisticsApi.jobs(),
      statisticsApi.matches()
    ]);
    overview.value = overviewData;
    applicationsStats.value = applicationData;
    jobsStats.value = jobData;
    matchesStats.value = matchData;
    await nextTick();
    renderCharts();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "统计数据加载失败");
  }
}

function toPieData(counts: Record<string, number>, labeler: (key: string) => string = (key) => key) {
  const entries = sortEntriesByCount(counts);
  return entries.length
    ? entries.map(([name, value]) => ({ name: labeler(name), value }))
    : [{ name: "暂无数据", value: 0, itemStyle: { color: "#d1d5db" } }];
}

function renderCharts() {
  disposeCharts();

  if (statusChartRef.value) {
    const chart = echarts.init(statusChartRef.value);
    const counts = normalizeStatusCounts(applicationsStats.value?.status_counts);
    chart.setOption({
      tooltip: {},
      xAxis: { type: "category", data: applicationStatusOrder.map((status) => applicationStatusLabels[status]) },
      yAxis: { type: "value", minInterval: 1 },
      series: [{ type: "bar", data: applicationStatusOrder.map((status) => counts[status] || 0), color: "#0f766e" }]
    });
    charts.push(chart);
  }

  if (sourceChartRef.value) {
    const chart = echarts.init(sourceChartRef.value);
    chart.setOption({
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["45%", "72%"],
          data: toPieData(jobsStats.value?.source_counts || {}, labelJobSource)
        }
      ]
    });
    charts.push(chart);
  }

  if (typeChartRef.value) {
    const chart = echarts.init(typeChartRef.value);
    const typeEntries = sortEntriesByCount(jobsStats.value?.type_counts || {});
    chart.setOption({
      tooltip: {},
      xAxis: { type: "category", data: typeEntries.map(([name]) => name) },
      yAxis: { type: "value", minInterval: 1 },
      series: [{ type: "bar", data: typeEntries.map(([, value]) => value), color: "#2563eb" }]
    });
    charts.push(chart);
  }

  if (matchChartRef.value) {
    const chart = echarts.init(matchChartRef.value);
    const ranges = matchesStats.value?.score_ranges || {};
    chart.setOption({
      tooltip: {},
      xAxis: { type: "category", data: [...MATCH_SCORE_RANGE_ORDER] },
      yAxis: { type: "value", minInterval: 1 },
      series: [
        {
          type: "bar",
          data: MATCH_SCORE_RANGE_ORDER.map((key) => ranges[key] || 0),
          color: "#b45309"
        }
      ]
    });
    charts.push(chart);
  }
}

function resizeCharts() {
  charts.forEach((chart) => chart.resize());
}

function disposeCharts() {
  charts.forEach((chart) => chart.dispose());
  charts = [];
}

onMounted(() => {
  load();
  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  disposeCharts();
});
</script>
