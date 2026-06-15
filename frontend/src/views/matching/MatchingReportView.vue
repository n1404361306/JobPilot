<template>
  <div>
    <PageHeader title="匹配报告" description="展示简历与岗位的匹配分、差距和建议。" />
    <div class="panel">
      <PendingFeature title="匹配分析接口待接入" :endpoints="['POST /api/ai/matching-analysis']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
