<template>
  <div>
    <PageHeader title="OCR 日志" description="查看简历、岗位截图等 OCR 解析记录。" />
    <section class="panel">
      <el-table v-loading="loading" :data="logs" size="large">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="source_type" label="来源类型" min-width="160" />
        <el-table-column prop="result_summary" label="结果摘要" min-width="280" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, ref } from "vue";
import { adminApi } from "@/api/modules";
import type { OcrLog } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const loading = ref(false);
const logs = ref<OcrLog[]>([]);

onMounted(async () => {
  loading.value = true;
  try {
    logs.value = await adminApi.ocrLogs();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "OCR 日志加载失败");
  } finally {
    loading.value = false;
  }
});
</script>
