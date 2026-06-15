<template>
  <div>
    <PageHeader title="自动投递" description="配置自动投递规则、站点、简历和目标岗位。" />
    <div class="panel">
      <PendingFeature title="自动投递接口待接入" :endpoints="['/api/delivery']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
