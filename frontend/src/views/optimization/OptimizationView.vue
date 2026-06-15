<template>
  <div>
    <PageHeader title="简历优化和岗位适配" description="针对目标岗位生成优化建议与适配版本。" />
    <div class="panel">
      <PendingFeature title="简历优化接口待接入" :endpoints="['POST /api/ai/resume-optimize', 'POST /api/ai/resume-adapt']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
