<template>
  <div>
    <PageHeader :title="isEdit ? '简历编辑器' : '新建简历'" description="桌面端左右编辑预览，移动端可通过步骤页签分段编辑。">
      <template #actions>
        <el-button @click="router.push({ name: 'resume-list' })">返回列表</el-button>
      </template>
    </PageHeader>

    <div class="grid-2">
      <section class="panel">
        <el-tabs v-model="activeTab" class="editor-tabs">
          <el-tab-pane label="基础信息" name="base">
            <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
              <el-form-item label="简历标题" prop="title">
                <el-input v-model="form.title" placeholder="例如：前端开发-校招版" />
              </el-form-item>
              <el-form-item label="默认简历">
                <el-switch v-model="form.is_default" />
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="正文内容" name="content">
            <el-input
              v-model="form.content"
              type="textarea"
              :rows="18"
              resize="vertical"
              placeholder="输入教育经历、项目经历、技能栈、实习经历等内容。"
            />
          </el-tab-pane>
        </el-tabs>
        <div class="form-actions">
          <el-button @click="router.push({ name: 'resume-list' })">取消</el-button>
          <el-button type="primary" :loading="saving" @click="save">保存简历</el-button>
        </div>
      </section>

      <section class="panel">
        <div class="panel-title">
          <h2>实时预览</h2>
          <el-tag type="info">A4 预览</el-tag>
        </div>
        <article class="resume-preview">
          <h2>{{ form.title || "未命名简历" }}</h2>
          <p>{{ form.content || "在左侧输入简历内容后，这里会实时展示预览。" }}</p>
        </article>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { resumeApi } from "@/api/modules";
import PageHeader from "@/components/PageHeader.vue";

const router = useRouter();
const route = useRoute();
const formRef = ref<FormInstance>();
const activeTab = ref("base");
const saving = ref(false);
const isEdit = computed(() => Boolean(route.params.id));

const form = reactive({
  title: "",
  content: "",
  file_url: null as string | null,
  is_default: false
});

const rules: FormRules<typeof form> = {
  title: [{ required: true, message: "请输入简历标题", trigger: "blur" }]
};

async function save() {
  await formRef.value?.validate();
  saving.value = true;
  try {
    if (isEdit.value) {
      await resumeApi.update(Number(route.params.id), form);
    } else {
      await resumeApi.create(form);
    }
    ElMessage.success("简历已保存");
    router.push({ name: "resume-list" });
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
    const resume = await resumeApi.get(Number(route.params.id));
    form.title = resume.title;
    form.content = resume.content;
    form.file_url = resume.file_url;
    form.is_default = resume.is_default;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "简历加载失败");
  }
});
</script>
