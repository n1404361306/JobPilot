<template>
  <el-form-item label="个人照片">
    <div class="photo-upload">
      <div v-if="modelValue" class="photo-preview">
        <img :src="modelValue" alt="个人照片" />
        <div class="photo-actions">
          <el-upload
            action="#"
            :auto-upload="false"
            accept=".jpg,.jpeg,.png,.webp"
            :show-file-list="false"
            :disabled="uploading"
            :on-change="handleChange"
          >
            <el-button size="small" :loading="uploading">更换照片</el-button>
          </el-upload>
          <el-button size="small" type="danger" link @click="clearPhoto">移除</el-button>
        </div>
      </div>

      <el-upload
        v-else
        drag
        action="#"
        :auto-upload="false"
        accept=".jpg,.jpeg,.png,.webp"
        :show-file-list="false"
        :disabled="uploading"
        :on-change="handleChange"
        class="photo-uploader"
      >
        <el-icon class="upload-icon"><Plus /></el-icon>
        <div class="upload-text">点击或拖拽上传证件照</div>
        <div class="upload-tip">支持 JPG / PNG / WebP，不超过 2MB</div>
      </el-upload>
    </div>
  </el-form-item>
</template>

<script setup lang="ts">
import { Plus } from "@element-plus/icons-vue";
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import { ref } from "vue";
import { compressImageFile } from "@/utils/photoUpload";

const modelValue = defineModel<string>("modelValue", { default: "" });
const uploading = ref(false);

async function handleChange(file: UploadFile) {
  if (!file.raw || uploading.value) {
    return;
  }
  uploading.value = true;
  try {
    modelValue.value = await compressImageFile(file.raw);
    ElMessage.success("照片已上传");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "照片上传失败");
  } finally {
    uploading.value = false;
  }
}

function clearPhoto() {
  modelValue.value = "";
}
</script>

<style scoped>
.photo-upload {
  width: 100%;
}

.photo-uploader :deep(.el-upload-dragger) {
  width: 100%;
  min-height: 148px;
  padding: 18px 12px;
}

.upload-icon {
  font-size: 28px;
  color: #94a3b8;
}

.upload-text {
  margin-top: 8px;
  font-size: 14px;
  color: #334155;
}

.upload-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
}

.photo-preview {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: #f8fafc;
}

.photo-preview img {
  width: 96px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 2px solid #fff;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
}

.photo-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}
</style>
