<template>
  <div>
    <PageHeader title="AI 制作简历模板" description="描述风格与布局需求，AI 生成模板并支持多轮修改；右侧可实时预览，也可直接编辑 HTML 源码。">
      <template #actions>
        <el-button :icon="Download" @click="downloadExample">下载示例模板</el-button>
        <el-button :icon="Document" @click="openTemplateDoc">模板要求文档</el-button>
        <el-button type="primary" :disabled="!templateContent.trim()" @click="openSaveDialog">保存模板</el-button>
      </template>
    </PageHeader>

    <div class="maker-grid">
      <section class="panel chat-panel">
        <div class="panel-title">
          <h2>与 AI 沟通</h2>
          <el-tag type="info">多轮修改</el-tag>
        </div>

        <el-collapse class="field-guide">
          <el-collapse-item title="模板必须包含的字段（点击查看）" name="fields">
            <ul class="field-list">
              <li v-for="field in RESUME_TEMPLATE_FIELD_SPECS" :key="field.key">
                <code>{{ "{" }}{{ "{" }}{{ field.key }}{{ "}" }}{{ "}" }}</code>
                <span>{{ field.label }}</span>
                <em>{{ field.required ? "必填" : "建议" }} · {{ field.format }}</em>
              </li>
            </ul>
          </el-collapse-item>
        </el-collapse>

        <div ref="chatRef" class="chat-messages">
          <article v-for="(item, index) in chatMessages" :key="index" class="chat-bubble" :class="item.role">
            <span class="chat-role">{{ item.role === "user" ? "你" : "AI" }}</span>
            <p>{{ item.content }}</p>
          </article>
          <el-empty v-if="chatMessages.length === 0" description="输入需求开始制作，例如：单栏技术风、蓝色标题、左侧放照片" />
        </div>

        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="5"
          placeholder="描述模板风格、配色、版式、适用岗位等，也可提出修改意见"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <div class="chat-actions">
          <el-button @click="resetSession">重新开始</el-button>
          <el-button type="primary" :loading="chatting" :disabled="!inputMessage.trim()" @click="sendMessage">
            发送给 AI
          </el-button>
        </div>
      </section>

      <section class="panel preview-panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="预览效果" name="preview">
            <div class="preview-shell">
              <ResumeStyledPreview
                v-if="templateContent.trim()"
                :snapshot="sampleSnapshot"
                template-id="custom:0"
                :custom-template-content="templateContent"
              />
              <el-empty v-else description="生成或编辑模板后在此预览" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="模板源码" name="source">
            <el-input
              v-model="templateContent"
              type="textarea"
              :rows="22"
              class="source-input"
              placeholder="可直接编辑 HTML 模板源码，修改后切换「预览效果」查看"
            />
          </el-tab-pane>
        </el-tabs>
      </section>
    </div>

    <el-dialog v-model="saveDialogVisible" title="保存简历模板" width="560px">
      <el-form label-position="top">
        <el-form-item label="模板名称" required>
          <el-input v-model="saveForm.name" placeholder="例如：AI 单栏技术模板" />
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input v-model="saveForm.description" placeholder="说明风格、适用场景" />
        </el-form-item>
        <el-form-item label="可见性">
          <el-radio-group v-model="saveForm.is_public">
            <el-radio-button :value="false">仅自己使用</el-radio-button>
            <el-radio-button :value="true">公开给其他用户</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveTemplate">确认保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Download, Document } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { nextTick, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { aiApi, templateApi } from "@/api/modules";
import type { ChatMessage, ResumeTemplate } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";
import ResumeStyledPreview from "@/components/ResumeStyledPreview.vue";
import { createSampleSnapshot } from "@/utils/resumeHelpers";
import { RESUME_TEMPLATE_FIELD_SPECS } from "@/utils/resumeTemplateFields";

const route = useRoute();
const router = useRouter();
const sampleSnapshot = createSampleSnapshot();
const chatRef = ref<HTMLElement>();
const chatting = ref(false);
const saving = ref(false);
const saveDialogVisible = ref(false);
const activeTab = ref("preview");
const inputMessage = ref("");
const templateContent = ref("");
const editingTemplateId = ref<number | null>(null);
const chatMessages = ref<ChatMessage[]>([]);
const saveForm = reactive({
  name: "",
  description: "",
  is_public: false
});

function downloadExample() {
  const link = document.createElement("a");
  link.href = "/docs/resume_template_example.html";
  link.download = "resume_template_example.html";
  link.rel = "noopener";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function openTemplateDoc() {
  window.open("/docs/resume_template_requirements.html", "_blank");
}

function resetSession() {
  chatMessages.value = [];
  inputMessage.value = "";
  templateContent.value = "";
  editingTemplateId.value = null;
  saveForm.name = "";
  saveForm.description = "";
  saveForm.is_public = false;
}

async function scrollChatToBottom() {
  await nextTick();
  if (chatRef.value) {
    chatRef.value.scrollTop = chatRef.value.scrollHeight;
  }
}

async function sendMessage() {
  const message = inputMessage.value.trim();
  if (!message || chatting.value) return;

  chatting.value = true;
  chatMessages.value.push({ role: "user", content: message });
  inputMessage.value = "";
  await scrollChatToBottom();

  try {
    const result = await aiApi.chatResumeTemplate({
      message,
      history: chatMessages.value.slice(0, -1),
      current_template: templateContent.value || null
    });
    const nextContent = String(result.data?.template_content || "");
    const summary = String(result.data?.summary || result.content || "模板已更新");
    if (nextContent) {
      templateContent.value = nextContent;
      activeTab.value = "preview";
    }
    chatMessages.value.push({ role: "assistant", content: summary });
    const missing = Array.isArray(result.data?.missing_fields) ? (result.data?.missing_fields as string[]) : [];
    if (missing.length) {
      ElMessage.warning(`模板缺少字段：${missing.join("、")}，可继续对话要求 AI 补全`);
    }
    await scrollChatToBottom();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "AI 生成失败");
    chatMessages.value.pop();
    inputMessage.value = message;
  } finally {
    chatting.value = false;
  }
}

function openSaveDialog() {
  if (!templateContent.value.trim()) {
    ElMessage.warning("请先生成或编辑模板内容");
    return;
  }
  if (!saveForm.name.trim()) {
    saveForm.name = editingTemplateId.value ? saveForm.name : "AI 简历模板";
  }
  saveDialogVisible.value = true;
}

async function saveTemplate() {
  if (!saveForm.name.trim()) {
    ElMessage.warning("请填写模板名称");
    return;
  }
  saving.value = true;
  try {
    const payload = {
      name: saveForm.name.trim(),
      description: saveForm.description.trim() || "AI 制作简历模板",
      content: templateContent.value,
      is_public: saveForm.is_public
    };
    if (editingTemplateId.value) {
      await templateApi.updateMine(editingTemplateId.value, payload);
      ElMessage.success("模板已更新");
    } else {
      await templateApi.createMine(payload);
      ElMessage.success("模板已保存");
    }
    saveDialogVisible.value = false;
    router.push({ name: "template-gallery" });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

function applyTemplate(template: ResumeTemplate) {
  editingTemplateId.value = template.id;
  templateContent.value = template.content;
  saveForm.name = template.name;
  saveForm.description = template.description || "";
  saveForm.is_public = template.is_public;
  chatMessages.value = [
    {
      role: "assistant",
      content: `已加载模板「${template.name}」。你可以继续与 AI 沟通修改，或在「模板源码」中直接编辑。`
    }
  ];
}

onMounted(async () => {
  const rawId = route.query.id;
  const id = typeof rawId === "string" ? Number(rawId) : NaN;
  if (!Number.isFinite(id) || id <= 0) return;
  try {
    const template = await templateApi.get(id);
    if (template.user_id) {
      applyTemplate(template);
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "模板加载失败");
  }
});
</script>

<style scoped>
.maker-grid {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 720px;
}

.field-guide {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.field-guide :deep(.el-collapse-item__header) {
  padding: 0 12px;
  height: 40px;
  font-size: 13px;
}

.field-guide :deep(.el-collapse-item__content) {
  padding: 0 12px 12px;
}

.field-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.field-list li {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px 8px;
  font-size: 12px;
  line-height: 1.4;
}

.field-list code {
  grid-row: span 2;
  padding: 2px 6px;
  border-radius: 4px;
  background: #f3f4f6;
  font-size: 11px;
  align-self: start;
}

.field-list em {
  grid-column: 2;
  color: #6b7280;
  font-style: normal;
  font-size: 11px;
}

.chat-messages {
  flex: 1;
  min-height: 420px;
  max-height: 520px;
  overflow-y: auto;
  padding: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f8fafc;
}

.chat-bubble {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.chat-bubble.user {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.chat-bubble.assistant {
  background: #fff;
}

.chat-role {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
}

.chat-bubble p {
  margin: 0;
  line-height: 1.6;
  white-space: pre-wrap;
}

.chat-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.preview-panel {
  min-height: 720px;
}

.preview-shell {
  overflow: auto;
  max-height: 640px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
}

.preview-shell :deep(.resume-doc) {
  margin: 0 auto;
  max-width: 820px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.source-input :deep(textarea) {
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
  line-height: 1.55;
}

@media (max-width: 1080px) {
  .maker-grid {
    grid-template-columns: 1fr;
  }

  .chat-panel,
  .preview-panel {
    min-height: auto;
  }

  .chat-messages {
    min-height: 280px;
    max-height: 360px;
  }
}
</style>
