<template>
  <div>
    <PageHeader title="简历预览和导出" description="预览简历内容，并通过浏览器打印或 PDF 导出。">
      <template #actions>
        <el-button :icon="Printer" @click="printPage">打印</el-button>
        <el-button type="primary" :icon="Download" @click="exportPdf">导出 PDF</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <el-skeleton v-if="loading" :rows="8" animated />
      <article v-else ref="previewRef" class="resume-preview">
        <h1>{{ resume?.title }}</h1>
        <p>{{ resume?.content }}</p>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Download, Printer } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import html2pdf from "html2pdf.js";
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { resumeApi } from "@/api/modules";
import type { Resume } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const route = useRoute();
const loading = ref(true);
const resume = ref<Resume | null>(null);
const previewRef = ref<HTMLElement>();

function printPage() {
  window.print();
}

async function exportPdf() {
  if (!previewRef.value) {
    return;
  }

  await html2pdf().from(previewRef.value).set({ filename: `${resume.value?.title || "resume"}.pdf` }).save();
}

onMounted(async () => {
  try {
    resume.value = await resumeApi.get(Number(route.params.id));
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "简历加载失败");
  } finally {
    loading.value = false;
  }
});
</script>
