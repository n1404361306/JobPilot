<template>
  <div>
    <PageHeader title="模拟面试" description="生成面试问题、记录作答，并展示评价结果。">
      <template #actions>
        <el-button :loading="questionLoading" @click="generateQuestions">生成题目</el-button>
        <el-button type="primary" :loading="evaluating" @click="evaluate">评价回答</el-button>
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <el-form label-position="top">
          <el-form-item label="面试背景来源">
            <el-segmented
              v-model="backgroundMode"
              :options="[
                { label: '选择已有岗位', value: 'job' },
                { label: '手动输入', value: 'manual' }
              ]"
            />
          </el-form-item>
          <el-form-item v-if="backgroundMode === 'job'" label="选择岗位">
            <el-select
              v-model="selectedJobId"
              filterable
              clearable
              class="full"
              placeholder="选择一个岗位作为面试背景"
              :loading="jobsLoading"
            >
              <el-option
                v-for="job in jobs"
                :key="job.id"
                :label="`${job.company} - ${job.title}`"
                :value="job.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item v-else label="面试背景">
            <el-input v-model="manualBackground" type="textarea" :rows="5" placeholder="输入目标岗位、简历亮点或想练习的方向" />
          </el-form-item>
          <el-form-item v-if="backgroundMode === 'job' && selectedJob" label="岗位信息">
            <div class="job-context">
              <strong>{{ selectedJob.company }} - {{ selectedJob.title }}</strong>
              <span>{{ [selectedJob.location, selectedJob.job_type, selectedJob.salary_range].filter(Boolean).join(" / ") || "暂无补充信息" }}</span>
              <p>{{ selectedJob.description || "暂无岗位描述" }}</p>
            </div>
          </el-form-item>
          <el-form-item label="选择题目">
            <el-select v-model="question" allow-create filterable placeholder="先生成题目或手动输入" class="full">
              <el-option v-for="item in questions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="我的回答">
            <el-input v-model="answer" type="textarea" :rows="8" />
          </el-form-item>
        </el-form>
      </section>

      <section class="panel">
        <el-empty v-if="!evaluation" description="提交回答后查看评价" />
        <pre v-else class="text-output">{{ displayText(evaluation) }}</pre>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { aiApi, jobApi } from "@/api/modules";
import type { AIResult, Job } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import { stripMarkdown } from "@/utils/textFormat";

const backgroundMode = ref<"job" | "manual">("job");
const manualBackground = ref("");
const selectedJobId = ref<number | null>(null);
const jobs = ref<Job[]>([]);
const jobsLoading = ref(false);
const question = ref("");
const answer = ref("");
const questions = ref<string[]>([]);
const evaluation = ref<AIResult | null>(null);
const questionLoading = ref(false);
const evaluating = ref(false);

const selectedJob = computed(() => jobs.value.find((job) => job.id === selectedJobId.value) || null);

const interviewBackground = computed(() => {
  if (backgroundMode.value === "job") {
    const job = selectedJob.value;
    if (!job) return "";
    return [
      `目标岗位：${job.title}`,
      `公司：${job.company}`,
      `地点：${job.location || "未填写"}`,
      `岗位类型：${job.job_type || "未填写"}`,
      `薪资：${job.salary_range || "未填写"}`,
      `标签：${job.tags || "未填写"}`,
      "",
      "岗位描述：",
      job.description || "未填写"
    ].join("\n");
  }
  return manualBackground.value.trim();
});

function displayText(result: AIResult | null) {
  return result ? stripMarkdown(result.content) : "";
}

async function loadJobs() {
  jobsLoading.value = true;
  try {
    jobs.value = await jobApi.list();
    if (!selectedJobId.value && jobs.value.length) {
      selectedJobId.value = jobs.value[0].id;
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "岗位加载失败");
  } finally {
    jobsLoading.value = false;
  }
}

async function generateQuestions() {
  if (!interviewBackground.value) {
    ElMessage.warning(backgroundMode.value === "job" ? "请先选择岗位" : "请先填写面试背景");
    return;
  }
  questionLoading.value = true;
  try {
    const result = await aiApi.interviewQuestions(
      interviewBackground.value,
      undefined,
      backgroundMode.value === "job" ? selectedJobId.value || undefined : undefined
    );
    const parsed = Array.isArray(result.data?.questions) ? (result.data.questions as string[]) : [];
    questions.value = parsed.length ? parsed.map((item) => stripMarkdown(item)) : displayText(result).split("\n").filter(Boolean);
    question.value = questions.value[0] || "";
    ElMessage.success("题目已生成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "生成失败");
  } finally {
    questionLoading.value = false;
  }
}

async function evaluate() {
  if (!question.value || !answer.value) {
    ElMessage.warning("请填写题目和回答");
    return;
  }
  evaluating.value = true;
  try {
    evaluation.value = await aiApi.evaluateAnswer({
      question: question.value,
      answer: answer.value,
      job_id: backgroundMode.value === "job" ? selectedJobId.value || undefined : undefined
    });
    ElMessage.success("评价已生成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "评价失败");
  } finally {
    evaluating.value = false;
  }
}

onMounted(loadJobs);
</script>

<style scoped>
.full {
  width: 100%;
}

.job-context {
  display: grid;
  gap: 6px;
  width: 100%;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: #f8fafc;
}

.job-context span {
  color: #64748b;
  font-size: 13px;
}

.job-context p {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  color: #475569;
  line-height: 1.6;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
}

.text-output {
  white-space: pre-wrap;
  line-height: 1.7;
  margin: 0;
}
</style>
