<template>
  <div>
    <PageHeader title="页面未找到" description="请从左侧导航进入已配置的功能页面。" />
    <div class="panel">
      <PendingFeature title="页面不存在" :endpoints="[]" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
