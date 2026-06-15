<template>
  <div>
    <PageHeader title="模板选择与用户模板上传" description="浏览已启用模板；用户自定义上传接口待后端接入。">
      <template #actions>
        <el-upload action="#" :auto-upload="false" accept=".html,.docx,.pdf">
          <el-button :icon="Upload">上传模板</el-button>
        </el-upload>
      </template>
    </PageHeader>

    <section class="grid-3">
      <article v-for="template in templates" :key="template.id" class="panel">
        <div class="panel-title">
          <h2>{{ template.name }}</h2>
          <el-tag v-if="template.enabled" type="success">启用</el-tag>
        </div>
        <p>{{ template.description || "暂无描述" }}</p>
        <div class="resume-preview template-preview">{{ template.content }}</div>
      </article>
    </section>

    <section v-if="!loading && !templates.length" class="panel">
      <EmptyState description="暂无可用模板" />
    </section>
    <section class="panel">
      <PendingFeature title="用户模板上传接口待接入" :endpoints="['POST /api/resume-templates/upload']" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { Upload } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { onMounted, ref } from "vue";
import { templateApi } from "@/api/modules";
import type { ResumeTemplate } from "@/api/types";
import EmptyState from "@/components/EmptyState.vue";
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";

const loading = ref(true);
const templates = ref<ResumeTemplate[]>([]);

onMounted(async () => {
  try {
    templates.value = await templateApi.list();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "模板加载失败");
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.template-preview {
  min-height: 220px;
  max-height: 260px;
  overflow: hidden;
  margin-top: 14px;
  font-size: 13px;
}
</style>
