<template>
  <div>
    <PageHeader title="岗位列表" description="管理岗位库，支持按状态和关键词筛选。">
      <template #actions>
        <el-button :icon="Upload" @click="router.push({ name: 'job-import' })">导入岗位</el-button>
        <el-button type="primary" :icon="Plus" @click="router.push({ name: 'job-new' })">新增岗位</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <el-form class="filter-bar" inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" clearable placeholder="岗位或公司" @keyup.enter="load" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
            <el-option label="招聘中" value="active" />
            <el-option label="已关闭" value="closed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">筛选</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="jobs" size="large">
        <el-table-column prop="title" label="岗位" min-width="160" />
        <el-table-column prop="company" label="公司" min-width="140" />
        <el-table-column prop="location" label="地点" min-width="120" />
        <el-table-column prop="salary_range" label="薪资" min-width="120" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag>{{ jobStatusLabels[row.status as JobStatus] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push({ name: 'job-detail', params: { id: row.id } })">详情</el-button>
            <el-button link type="primary" @click="createApplication(row)">加入投递</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Plus, Upload } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { applicationApi, jobApi } from "@/api/modules";
import type { Job, JobStatus } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import { jobStatusLabels } from "@/utils/status";

const router = useRouter();
const loading = ref(false);
const jobs = ref<Job[]>([]);
const filters = reactive({ keyword: "", status: "" });

async function load() {
  loading.value = true;
  try {
    jobs.value = await jobApi.list({
      keyword: filters.keyword || undefined,
      status: filters.status || undefined
    });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "岗位加载失败");
  } finally {
    loading.value = false;
  }
}

async function createApplication(job: Job) {
  await applicationApi.create({ job_id: job.id, status: "pending", channel: "手动加入" });
  ElMessage.success("已加入投递看板");
}

async function remove(job: Job) {
  await ElMessageBox.confirm(`确认删除「${job.title}」？`, "删除岗位", { type: "warning" });
  await jobApi.remove(job.id);
  ElMessage.success("已删除");
  await load();
}

onMounted(load);
</script>

<style scoped>
.filter-bar {
  margin-bottom: 12px;
}
</style>
