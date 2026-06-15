<template>
  <div>
    <PageHeader title="Prompt 管理" description="维护 AI 提示词模板和版本。" />
    <div class="panel">
      <PendingFeature title="Prompt 管理接口待接入" :endpoints="['/api/admin/prompts']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
