<template>
  <div>
    <PageHeader title="投递站点配置" description="维护自动投递目标站点、账号策略和限速规则。" />
    <div class="panel">
      <PendingFeature title="投递站点配置接口待接入" :endpoints="['/api/admin/delivery-sites', '/api/delivery/sites']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
