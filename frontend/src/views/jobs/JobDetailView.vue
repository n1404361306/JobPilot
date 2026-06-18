<template>
  <div>
    <PageHeader :title="isEdit ? '岗位详情' : '新增岗位'" description="维护岗位基础信息、来源记录、标签、截止时间和状态。">
      <template #actions>
        <el-button @click="router.push({ name: 'job-list' })">返回列表</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="grid-2">
          <el-form-item label="岗位名称" prop="title">
            <el-input v-model="form.title" />
          </el-form-item>
          <el-form-item label="公司" prop="company">
            <el-input v-model="form.company" />
          </el-form-item>
          <el-form-item label="地点">
            <el-input v-model="form.location" />
          </el-form-item>
          <el-form-item label="薪资范围">
            <el-input v-model="form.salary_range" />
          </el-form-item>
          <el-form-item label="岗位类型">
            <el-input v-model="form.job_type" placeholder="后端开发 / 算法 / AI 应用" />
          </el-form-item>
          <el-form-item label="截止时间">
            <el-date-picker v-model="form.deadline" value-format="YYYY-MM-DD" type="date" style="width: 100%" />
          </el-form-item>
          <el-form-item label="来源类型">
            <el-input v-model="form.source_type" placeholder="manual / text / url / file / image / batch_text" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status" style="width: 100%">
              <el-option label="招聘中" value="active" />
              <el-option label="已关闭" value="closed" />
              <el-option label="已归档" value="archived" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="来源链接">
          <el-input v-model="form.source_url" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.is_favorite">收藏岗位</el-checkbox>
        </el-form-item>
        <el-form-item label="岗位描述">
          <el-input v-model="form.description" type="textarea" :rows="12" />
        </el-form-item>
      </el-form>
      <div class="form-actions">
        <el-button @click="router.push({ name: 'job-list' })">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存岗位</el-button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { jobApi } from "@/api/modules";
import type { JobPayload, JobStatus } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const router = useRouter();
const route = useRoute();
const formRef = ref<FormInstance>();
const saving = ref(false);
const isEdit = computed(() => Boolean(route.params.id));

const form = reactive({
  title: "",
  company: "",
  location: "",
  salary_range: "",
  source_url: "",
  source_type: "manual",
  job_type: "",
  deadline: "",
  tags: "",
  is_favorite: false,
  description: "",
  status: "active" as JobStatus
});

const rules: FormRules<typeof form> = {
  title: [{ required: true, message: "请输入岗位名称", trigger: "blur" }],
  company: [{ required: true, message: "请输入公司", trigger: "blur" }]
};

function buildPayload(): JobPayload {
  return {
    title: form.title,
    company: form.company,
    location: form.location || null,
    salary_range: form.salary_range || null,
    source_url: form.source_url || null,
    source_type: form.source_type || null,
    job_type: form.job_type || null,
    deadline: form.deadline || null,
    tags: form.tags || null,
    is_favorite: form.is_favorite,
    description: form.description || null,
    status: form.status
  };
}

async function save() {
  await formRef.value?.validate();
  saving.value = true;
  try {
    if (isEdit.value) {
      await jobApi.update(Number(route.params.id), buildPayload());
    } else {
      await jobApi.create(buildPayload());
    }
    ElMessage.success("岗位已保存");
    router.push({ name: "job-list" });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  if (!isEdit.value) {
    return;
  }

  try {
    const job = await jobApi.get(Number(route.params.id));
    Object.assign(form, {
      title: job.title,
      company: job.company,
      location: job.location || "",
      salary_range: job.salary_range || "",
      source_url: job.source_url || "",
      source_type: job.source_type || "",
      job_type: job.job_type || "",
      deadline: job.deadline || "",
      tags: job.tags || "",
      is_favorite: Boolean(job.is_favorite),
      description: job.description || "",
      status: job.status as JobStatus
    });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "岗位加载失败");
  }
});
</script>
