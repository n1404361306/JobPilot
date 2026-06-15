<template>
  <div>
    <PageHeader title="系统配置" description="查看和修改后端系统配置项。" />
    <section class="panel">
      <el-table v-loading="loading" :data="configs" size="large">
        <el-table-column prop="key" label="配置键" min-width="200" />
        <el-table-column prop="value" label="配置值" min-width="260" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" title="编辑配置" width="560px">
      <el-form label-position="top">
        <el-form-item label="配置键">
          <el-input v-model="form.key" disabled />
        </el-form-item>
        <el-form-item label="配置值">
          <el-input v-model="form.value" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, reactive, ref } from "vue";
import { adminApi } from "@/api/modules";
import type { SystemConfig } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const loading = ref(false);
const dialogVisible = ref(false);
const configs = ref<SystemConfig[]>([]);
const form = reactive({ key: "", value: "" });

async function load() {
  loading.value = true;
  try {
    configs.value = await adminApi.systemConfigs();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "系统配置加载失败");
  } finally {
    loading.value = false;
  }
}

function openDialog(config: SystemConfig) {
  form.key = config.key;
  form.value = config.value;
  dialogVisible.value = true;
}

async function save() {
  await adminApi.updateSystemConfig(form.key, form.value);
  ElMessage.success("配置已更新");
  dialogVisible.value = false;
  await load();
}

onMounted(load);
</script>
