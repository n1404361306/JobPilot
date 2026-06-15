<template>
  <div>
    <PageHeader title="AI 日志" description="查看最近 AI 调用记录、Token、耗时和错误信息。" />
    <section class="panel">
      <el-table v-loading="loading" :data="logs" size="large">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="prompt_type" label="类型" min-width="140" />
        <el-table-column prop="model_name" label="模型" min-width="140" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="120" />
        <el-table-column prop="input_tokens" label="输入" width="100" />
        <el-table-column prop="output_tokens" label="输出" width="100" />
        <el-table-column prop="error_message" label="错误" min-width="180" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, ref } from "vue";
import { adminApi } from "@/api/modules";
import type { AiLog } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const loading = ref(false);
const logs = ref<AiLog[]>([]);

onMounted(async () => {
  loading.value = true;
  try {
    logs.value = await adminApi.aiLogs();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "AI 日志加载失败");
  } finally {
    loading.value = false;
  }
});
</script>
