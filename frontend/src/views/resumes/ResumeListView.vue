<template>
  <div>
    <PageHeader title="简历列表和版本管理" description="管理不同岗位方向的简历版本，并设置默认简历。">
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="router.push({ name: 'resume-new' })">新建简历</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <el-skeleton v-if="loading" :rows="5" animated />
      <el-table v-else-if="resumes.length" :data="resumes" size="large">
        <el-table-column prop="title" label="简历标题" min-width="180" />
        <el-table-column label="默认版本" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success">默认</el-tag>
            <el-button v-else link type="primary" @click="setDefault(row)">设为默认</el-button>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push({ name: 'resume-edit', params: { id: row.id } })">编辑</el-button>
            <el-button link type="primary" @click="router.push({ name: 'resume-preview', params: { id: row.id } })">预览</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else description="暂无简历版本">
        <el-button type="primary" @click="router.push({ name: 'resume-new' })">创建第一份简历</el-button>
      </EmptyState>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Plus } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { resumeApi } from "@/api/modules";
import type { Resume } from "@/api/types";
import EmptyState from "@/components/EmptyState.vue";
import PageHeader from "@/components/PageHeader.vue";
import { formatDateTime } from "@/utils/status";

const router = useRouter();
const loading = ref(true);
const resumes = ref<Resume[]>([]);

async function load() {
  loading.value = true;
  try {
    resumes.value = await resumeApi.list();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "简历加载失败");
  } finally {
    loading.value = false;
  }
}

async function setDefault(resume: Resume) {
  await resumeApi.update(resume.id, { is_default: true });
  ElMessage.success("已设置默认简历");
  await load();
}

async function remove(resume: Resume) {
  await ElMessageBox.confirm(`确认删除「${resume.title}」？`, "删除简历", { type: "warning" });
  await resumeApi.remove(resume.id);
  ElMessage.success("已删除");
  await load();
}

onMounted(load);
</script>
