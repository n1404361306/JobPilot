<template>
  <div>
    <PageHeader title="求职报告" description="生成周报、月报和阶段性复盘报告。" />
    <div class="panel">
      <PendingFeature title="报告生成接口待接入" :endpoints="['GET /api/reports', 'POST /api/ai/weekly-report']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
