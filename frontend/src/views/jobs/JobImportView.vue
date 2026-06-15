<template>
  <div>
    <PageHeader title="岗位导入" description="支持文本、URL、文件和截图入口；当前可将手动整理的岗位信息保存到岗位库。">
      <template #actions>
        <el-button type="primary" :icon="Check" :loading="saving" @click="saveJob">保存岗位</el-button>
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="文本" name="text">
            <el-input v-model="rawText" type="textarea" :rows="12" placeholder="粘贴岗位 JD、职责、要求等文本。" />
          </el-tab-pane>
          <el-tab-pane label="URL" name="url">
            <el-input v-model="form.source_url" placeholder="https://example.com/job/123" />
          </el-tab-pane>
          <el-tab-pane label="文件" name="file">
            <el-upload drag action="#" :auto-upload="false" accept=".pdf,.doc,.docx,.txt">
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">选择岗位文件</div>
            </el-upload>
          </el-tab-pane>
          <el-tab-pane label="截图" name="screenshot">
            <el-upload drag action="#" :auto-upload="false" accept=".png,.jpg,.jpeg,.webp">
              <el-icon class="el-icon--upload"><Picture /></el-icon>
              <div class="el-upload__text">选择岗位截图</div>
            </el-upload>
          </el-tab-pane>
        </el-tabs>
        <PendingFeature title="自动解析接口待接入" :endpoints="['POST /api/jobs/import']" />
      </section>

      <section class="panel">
        <div class="panel-title">
          <h2>岗位信息</h2>
          <el-tag type="info">可手动保存</el-tag>
        </div>
        <el-form label-position="top">
          <el-form-item label="岗位名称">
            <el-input v-model="form.title" />
          </el-form-item>
          <el-form-item label="公司">
            <el-input v-model="form.company" />
          </el-form-item>
          <el-form-item label="地点">
            <el-input v-model="form.location" />
          </el-form-item>
          <el-form-item label="薪资范围">
            <el-input v-model="form.salary_range" />
          </el-form-item>
          <el-form-item label="岗位描述">
            <el-input v-model="form.description" type="textarea" :rows="8" />
          </el-form-item>
        </el-form>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check, Picture, UploadFilled } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { jobApi } from "@/api/modules";
import PageHeader from "@/components/PageHeader.vue";
import PendingFeature from "@/components/PendingFeature.vue";

const router = useRouter();
const activeTab = ref("text");
const rawText = ref("");
const saving = ref(false);
const form = reactive({
  title: "",
  company: "",
  location: "",
  salary_range: "",
  source_url: "",
  description: "",
  status: "active" as const
});

watch(rawText, (value) => {
  if (!form.description) {
    form.description = value;
  }
});

async function saveJob() {
  if (!form.title || !form.company) {
    ElMessage.warning("请填写岗位名称和公司");
    return;
  }

  saving.value = true;
  try {
    await jobApi.create(form);
    ElMessage.success("岗位已保存");
    router.push({ name: "job-list" });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}
</script>
