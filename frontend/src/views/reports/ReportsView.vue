<template>
  <div>
    <PageHeader title="AI 总结" description="基于求职数据生成阶段性复盘总结，可删除历史记录。">
      <template #actions>
        <el-button type="primary" :loading="generating" @click="generate">生成 AI 总结</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <el-empty v-if="reports.length === 0" description="暂无总结，点击右上角生成" />
      <el-timeline v-else>
        <el-timeline-item v-for="report in reports" :key="report.id" :timestamp="report.created_at">
          <div class="report-item">
            <div class="report-header">
              <h3>{{ report.title }}</h3>
              <el-button link type="danger" :loading="deletingId === report.id" @click="remove(report.id)">
                删除
              </el-button>
            </div>
            <p class="report-content">{{ displayContent(report.content) }}</p>
          </div>
        </el-timeline-item>
      </el-timeline>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from "element-plus";
import { onMounted, ref } from "vue";
import { reportApi } from "@/api/modules";
import type { Report } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import { stripMarkdown } from "@/utils/textFormat";

const reports = ref<Report[]>([]);
const generating = ref(false);
const deletingId = ref<number | null>(null);

function displayContent(content: string) {
  return stripMarkdown(content);
}

async function load() {
  reports.value = await reportApi.list();
}

async function generate() {
  generating.value = true;
  try {
    await reportApi.weekly();
    await load();
    ElMessage.success("总结已生成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "生成失败");
  } finally {
    generating.value = false;
  }
}

async function remove(id: number) {
  try {
    await ElMessageBox.confirm("确定删除这条总结吗？", "删除确认", { type: "warning" });
  } catch {
    return;
  }

  deletingId.value = id;
  try {
    await reportApi.remove(id);
    reports.value = reports.value.filter((item) => item.id !== id);
    ElMessage.success("已删除");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "删除失败");
  } finally {
    deletingId.value = null;
  }
}

onMounted(load);
</script>

<style scoped>
.report-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.report-header h3 {
  margin: 0;
}

.report-content {
  white-space: pre-wrap;
  line-height: 1.7;
  margin: 0;
}
</style>
