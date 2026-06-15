<template>
  <el-result
    icon="info"
    :title="title"
    sub-title="该功能入口已在前端完成，等待后端接口接入后即可替换为真实请求。"
  >
    <template #extra>
      <el-space wrap>
        <el-tag v-for="endpoint in endpoints" :key="endpoint" type="info">{{ endpoint }}</el-tag>
      </el-space>
    </template>
  </el-result>
</template>

<script setup lang="ts">
defineProps<{
  title?: string;
  endpoints?: string[];
}>();
</script>
