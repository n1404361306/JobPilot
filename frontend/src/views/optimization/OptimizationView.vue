<template>
  <div>
    <PageHeader title="简历优化和岗位适配" description="针对目标岗位生成优化建议与适配版本。">
      <template #actions>
        <el-button type="primary" :loading="loading" @click="run">生成建议</el-button>
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
          <el-form-item label="补充要求">
            <el-input v-model="extra" type="textarea" :rows="6" placeholder="例如：突出 Java 后端、数据库优化、团队协作" />
          </el-form-item>
        </el-form>
      </section>

      <section class="panel">
        <el-tabs>
          <el-tab-pane label="优化建议">
            <el-empty v-if="!optimize" description="暂无优化建议" />
            <pre v-else class="text-output">{{ displayText(optimize) }}</pre>
          </el-tab-pane>
          <el-tab-pane label="岗位适配">
            <el-empty v-if="!adapt" description="暂无适配建议" />
            <pre v-else class="text-output">{{ displayText(adapt) }}</pre>
          </el-tab-pane>
        </el-tabs>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, reactive, ref } from "vue";
import { aiApi, jobApi, resumeApi } from "@/api/modules";
import type { AIResult, Job, Resume } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import { stripMarkdown } from "@/utils/textFormat";

function displayText(result: AIResult | null) {
  return result ? stripMarkdown(result.content) : "";
}

const resumes = ref<Resume[]>([]);
const jobs = ref<Job[]>([]);
const optimize = ref<AIResult | null>(null);
const adapt = ref<AIResult | null>(null);
const loading = ref(false);
const extra = ref("");
const form = reactive<{ resume_id?: number; job_id?: number }>({});

onMounted(async () => {
  [resumes.value, jobs.value] = await Promise.all([resumeApi.list(), jobApi.list()]);
});

async function run() {
  if (!form.resume_id || !form.job_id) {
    ElMessage.warning("请选择简历和岗位");
    return;
  }
  const resume = resumes.value.find((item) => item.id === form.resume_id);
  const job = jobs.value.find((item) => item.id === form.job_id);
  const text = `${resume?.content || ""}\n\n目标岗位：${job?.description || job?.title || ""}\n${extra.value}`;
  loading.value = true;
  try {
    [optimize.value, adapt.value] = await Promise.all([
      aiApi.optimizeResume(text, form.resume_id, form.job_id),
      aiApi.adaptResume(text, form.resume_id, form.job_id)
    ]);
    ElMessage.success("建议已生成");
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

.text-output {
  white-space: pre-wrap;
  line-height: 1.7;
  margin: 0;
}
</style>
