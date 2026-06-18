<template>
  <div>
    <PageHeader title="管理员模板管理" description="维护简历模板内容、描述和启用状态。">
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增模板</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <el-table v-loading="loading" :data="templates" size="large">
        <el-table-column prop="name" label="模板名称" min-width="160" />
        <el-table-column prop="description" label="描述" min-width="220" />
        <el-table-column label="启用" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? "启用" : "停用" }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="公开" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'warning' : 'info'">{{ row.is_public ? "公开" : "私有" }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑模板' : '新增模板'" width="720px">
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" />
        </el-form-item>
        <el-form-item label="模板内容">
          <el-input v-model="form.content" type="textarea" :rows="12" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
        <el-form-item label="公开给所有用户">
          <el-switch v-model="form.is_public" />
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
import { Plus } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { onMounted, reactive, ref } from "vue";
import { templateApi } from "@/api/modules";
import type { ResumeTemplate } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const loading = ref(false);
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const templates = ref<ResumeTemplate[]>([]);
const form = reactive({
  name: "",
  description: "",
  content: "",
  enabled: true,
  is_public: true
});

async function load() {
  loading.value = true;
  try {
    templates.value = await templateApi.manage();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "模板加载失败");
  } finally {
    loading.value = false;
  }
}

function openDialog(template?: ResumeTemplate) {
  editingId.value = template?.id ?? null;
  Object.assign(form, {
    name: template?.name || "",
    description: template?.description || "",
    content: template?.content || "",
    enabled: template?.enabled ?? true,
    is_public: template?.is_public ?? true
  });
  dialogVisible.value = true;
}

async function save() {
  if (!form.name || !form.content) {
    ElMessage.warning("请填写名称和内容");
    return;
  }

  if (editingId.value) {
    await templateApi.update(editingId.value, form);
  } else {
    await templateApi.create(form);
  }
  ElMessage.success("模板已保存");
  dialogVisible.value = false;
  await load();
}

async function remove(template: ResumeTemplate) {
  await ElMessageBox.confirm(`确认删除「${template.name}」？`, "删除模板", { type: "warning" });
  await templateApi.remove(template.id);
  ElMessage.success("已删除");
  await load();
}

onMounted(load);
</script>
