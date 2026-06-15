<template>
  <div>
    <PageHeader title="模拟面试" description="生成面试问题、记录作答，并展示评价结果。" />
    <div class="panel">
      <PendingFeature title="模拟面试接口待接入" :endpoints="['POST /api/interviews', 'POST /api/ai/interview-evaluate']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
