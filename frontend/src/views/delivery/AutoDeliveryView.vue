<template>
  <div>
    <PageHeader title="自动投递" description="维护投递档案，生成字段预览，并执行投递任务。">
      <template #actions>
        <el-button :loading="savingProfile" @click="saveProfile">保存档案</el-button>
        <el-button type="primary" :loading="taskLoading" @click="createAndRunTask">创建并执行</el-button>
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <div class="panel-title"><h2>标准投递信息</h2></div>
        <el-form label-position="top">
          <el-form-item label="姓名"><el-input v-model="profile.real_name" /></el-form-item>
          <el-form-item label="电话"><el-input v-model="profile.phone" /></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="profile.email" /></el-form-item>
          <el-form-item label="学校"><el-input v-model="profile.school" /></el-form-item>
          <el-form-item label="专业"><el-input v-model="profile.major" /></el-form-item>
          <el-form-item label="常用问答"><el-input v-model="profile.common_answers" type="textarea" :rows="4" /></el-form-item>
        </el-form>
      </section>

      <section class="panel">
        <div class="panel-title"><h2>任务配置</h2></div>
        <el-form label-position="top">
          <el-form-item label="岗位">
            <el-select v-model="task.job_id" class="full" placeholder="选择岗位">
              <el-option v-for="job in jobs" :key="job.id" :label="`${job.company} - ${job.title}`" :value="job.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="简历">
            <el-select v-model="task.resume_id" clearable class="full" placeholder="选择简历">
              <el-option v-for="resume in resumes" :key="resume.id" :label="resume.title" :value="resume.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="站点名称"><el-input v-model="task.site_name" /></el-form-item>
          <el-form-item label="投递链接"><el-input v-model="task.target_url" /></el-form-item>
        </el-form>
        <el-divider />
        <el-descriptions v-if="currentTask" :column="1" border>
          <el-descriptions-item label="任务状态">{{ currentTask.task_status }}</el-descriptions-item>
          <el-descriptions-item label="字段预览"><pre>{{ previewText }}</pre></el-descriptions-item>
          <el-descriptions-item label="执行日志">
            <div v-for="log in logs" :key="log.id">{{ log.created_at }} {{ log.message }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";
import { deliveryApi, jobApi, resumeApi } from "@/api/modules";
import type { DeliveryTask, DeliveryTaskLog, Job, Resume } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const jobs = ref<Job[]>([]);
const resumes = ref<Resume[]>([]);
const currentTask = ref<DeliveryTask | null>(null);
const preview = ref<Record<string, unknown> | null>(null);
const logs = ref<DeliveryTaskLog[]>([]);
const savingProfile = ref(false);
const taskLoading = ref(false);
const profile = reactive({
  real_name: "",
  phone: "",
  email: "",
  school: "",
  major: "",
  common_answers: ""
});
const task = reactive<{ job_id?: number; resume_id?: number | null; site_name: string; target_url: string }>({
  resume_id: null,
  site_name: "",
  target_url: ""
});
const previewText = computed(() => JSON.stringify(preview.value, null, 2));

onMounted(async () => {
  const [profileData, resumeData, jobData] = await Promise.all([deliveryApi.profile(), resumeApi.list(), jobApi.list()]);
  Object.assign(profile, profileData);
  resumes.value = resumeData;
  jobs.value = jobData;
});

async function saveProfile() {
  savingProfile.value = true;
  try {
    Object.assign(profile, await deliveryApi.updateProfile(profile));
    ElMessage.success("投递档案已保存");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    savingProfile.value = false;
  }
}

async function createAndRunTask() {
  if (!task.job_id) {
    ElMessage.warning("请选择岗位");
    return;
  }
  taskLoading.value = true;
  try {
    const created = await deliveryApi.createTask(task as { job_id: number; resume_id?: number | null; site_name?: string; target_url?: string });
    const previewResult = await deliveryApi.previewTask(created.id);
    preview.value = previewResult.preview;
    currentTask.value = await deliveryApi.executeTask(created.id);
    logs.value = await deliveryApi.logs(created.id);
    ElMessage.success("投递任务已完成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "执行失败");
  } finally {
    taskLoading.value = false;
  }
}
</script>

<style scoped>
.full {
  width: 100%;
}

pre {
  white-space: pre-wrap;
  margin: 0;
}
</style>
