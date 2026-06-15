<template>
  <div>
    <PageHeader title="文字生成简历" description="根据自然语言描述生成结构化简历内容。" />
    <div class="panel">
      <PendingFeature title="AI 生成接口待接入" :endpoints="['POST /api/ai/resume-generate']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
