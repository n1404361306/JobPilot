<template>
  <div class="auth-page">
    <section class="auth-panel">
      <div class="auth-brand">
        <span>J</span>
        <strong>JobPilot</strong>
      </div>
      <h1>创建账号</h1>
      <p>注册后可管理简历、岗位和投递记录。</p>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" size="large" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" size="large" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" size="large" type="password" show-password />
        </el-form-item>
        <el-button type="primary" size="large" class="auth-submit" :loading="loading" @click="handleSubmit">
          注册并登录
        </el-button>
      </el-form>

      <p class="auth-switch">
        已有账号？
        <RouterLink :to="{ name: 'login' }">去登录</RouterLink>
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

const router = useRouter();
const userStore = useUserStore();
const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  username: "",
  email: "",
  password: ""
});

const rules: FormRules<typeof form> = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, message: "用户名至少 3 个字符", trigger: "blur" }
  ],
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "邮箱格式不正确", trigger: "blur" }
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码至少 6 位", trigger: "blur" }
  ]
};

async function handleSubmit() {
  await formRef.value?.validate();
  loading.value = true;
  try {
    await userStore.register(form.username, form.email, form.password);
    router.push({ name: "dashboard" });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "注册失败");
  } finally {
    loading.value = false;
  }
}
</script>
