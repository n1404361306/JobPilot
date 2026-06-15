<template>
  <div>
    <PageHeader
      title="简历上传解析"
      description="支持 PDF、DOCX 和图片文件选择；解析接口接入后可自动生成简历版本。"
    />
    <section class="panel">
      <el-upload drag action="#" :auto-upload="false" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.webp">
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到这里，或点击选择</div>
        <template #tip>
          <div class="el-upload__tip">PDF、DOCX、PNG、JPG、WEBP</div>
        </template>
      </el-upload>
      <PendingFeature title="OCR/解析接口待接入" :endpoints="['POST /api/ai/resume-parse', 'POST /api/ocr']" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { UploadFilled } from "@element-plus/icons-vue";
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";
</script>
