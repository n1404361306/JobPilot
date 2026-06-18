<template>
  <div>
    <PageHeader title="Prompt 管理" description="维护 AI 提示词模板和版本。">
      <template #actions>
        <el-button type="primary" :loading="saving" @click="create">新增模板</el-button>
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <el-form label-position="top">
          <el-form-item label="模板编码"><el-input v-model="form.template_code" /></el-form-item>
          <el-form-item label="模板名称"><el-input v-model="form.template_name" /></el-form-item>
          <el-form-item label="版本"><el-input-number v-model="form.version" :min="1" /></el-form-item>
          <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
          <el-form-item label="模板内容"><el-input v-model="form.template_content" type="textarea" :rows="8" /></el-form-item>
        </el-form>
      </section>

      <section class="panel">
        <el-table :data="prompts" stripe>
          <el-table-column prop="template_code" label="编码" width="150" />
          <el-table-column prop="template_name" label="名称" />
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="enabled" label="启用" width="80">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? "是" : "否" }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, reactive, ref } from "vue";
import { adminApi } from "@/api/modules";
import type { PromptTemplate } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const prompts = ref<PromptTemplate[]>([]);
const saving = ref(false);
const form = reactive({
  template_code: "",
  template_name: "",
  template_content: "",
  version: 1,
  enabled: true
});

async function load() {
  prompts.value = await adminApi.prompts();
}

async function create() {
  if (!form.template_code || !form.template_name || !form.template_content) {
    ElMessage.warning("请填写完整模板信息");
    return;
  }
  saving.value = true;
  try {
    await adminApi.createPrompt(form);
    Object.assign(form, { template_code: "", template_name: "", template_content: "", version: 1, enabled: true });
    await load();
    ElMessage.success("Prompt 模板已新增");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>
