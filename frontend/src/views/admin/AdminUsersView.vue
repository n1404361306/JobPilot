<template>
  <div>
    <PageHeader title="管理员用户管理" description="查看用户账号并启用/停用账号。" />
    <section class="panel">
      <el-table v-loading="loading" :data="users" size="large">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_superuser ? 'warning' : 'info'">{{ row.is_superuser ? "管理员" : "用户" }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="140">
          <template #default="{ row }">
            <el-switch :model-value="row.is_active" @change="handleStatusChange(row, $event)" />
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, ref } from "vue";
import { adminApi } from "@/api/modules";
import type { AdminUser } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const loading = ref(false);
const users = ref<AdminUser[]>([]);

async function load() {
  loading.value = true;
  try {
    users.value = await adminApi.users();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "用户加载失败");
  } finally {
    loading.value = false;
  }
}

function handleStatusChange(user: AdminUser, value: string | number | boolean) {
  updateStatus(user, Boolean(value));
}

async function updateStatus(user: AdminUser, isActive: boolean) {
  await adminApi.updateUserStatus(user.id, isActive);
  ElMessage.success("状态已更新");
  await load();
}

onMounted(load);
</script>
