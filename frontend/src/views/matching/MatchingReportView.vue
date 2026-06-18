<template>
  <div>
    <PageHeader title="匹配报告" description="计算简历与岗位的匹配分、优势和差距。">
      <template #actions>
        <el-button type="primary" :loading="loading" @click="calculate">生成匹配报告</el-button>
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <el-form label-position="top">
          <el-form-item label="简历">
            <el-select v-model="form.resume_id" placeholder="选择简历" class="full">
              <el-option v-for="resume in resumes" :key="resume.id" :label="resume.title" :value="resume.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="岗位">
            <el-select v-model="form.job_id" placeholder="选择岗位" class="full">
              <el-option v-for="job in jobs" :key="job.id" :label="`${job.company} - ${job.title}`" :value="job.id" />
            </el-select>
          </el-form-item>
        </el-form>
      </section>

      <section class="panel">
        <el-empty v-if="!report" description="选择简历和岗位后生成报告" />
        <div v-else>
          <el-progress type="dashboard" :percentage="report.score" />
          <h2>{{ report.summary }}</h2>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="优势">{{ report.strengths }}</el-descriptions-item>
            <el-descriptions-item label="差距">{{ report.gaps }}</el-descriptions-item>
            <el-descriptions-item label="建议">{{ report.suggestions }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, reactive, ref } from "vue";
import { jobApi, matchingApi, resumeApi } from "@/api/modules";
import type { Job, MatchReport, Resume } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const resumes = ref<Resume[]>([]);
const jobs = ref<Job[]>([]);
const report = ref<MatchReport | null>(null);
const loading = ref(false);
const form = reactive<{ resume_id?: number; job_id?: number }>({});

onMounted(async () => {
  [resumes.value, jobs.value] = await Promise.all([resumeApi.list(), jobApi.list()]);
});

async function calculate() {
  if (!form.resume_id || !form.job_id) {
    ElMessage.warning("请选择简历和岗位");
    return;
  }
  loading.value = true;
  try {
    report.value = await matchingApi.calculate({ resume_id: form.resume_id, job_id: form.job_id });
    ElMessage.success("报告已生成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "生成失败");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.full {
  width: 100%;
}
</style>
