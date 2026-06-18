<template>
  <div>
    <PageHeader title="投递站点配置" description="维护自动投递目标站点、账号策略和限速规则。">
      <template #actions>
        <el-button @click="addSite">新增站点</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <el-table :data="sites" stripe>
        <el-table-column label="站点名称" min-width="160">
          <template #default="{ row }"><el-input v-model="row.site_name" /></template>
        </el-table-column>
        <el-table-column label="登录/投递链接" min-width="240">
          <template #default="{ row }"><el-input v-model="row.login_url" /></template>
        </el-table-column>
        <el-table-column label="限速说明" min-width="220">
          <template #default="{ row }"><el-input v-model="row.rate_limit_note" /></template>
        </el-table-column>
        <el-table-column label="启用" width="90">
          <template #default="{ row }"><el-switch v-model="row.enabled" /></template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, ref } from "vue";
import { adminApi } from "@/api/modules";
import type { DeliverySite } from "@/api/types";
import PageHeader from "@/components/PageHeader.vue";

const sites = ref<DeliverySite[]>([]);
const saving = ref(false);

function addSite() {
  sites.value.push({ site_name: "", login_url: "", enabled: true, rate_limit_note: "遇到验证码或登录时暂停" });
}

async function load() {
  sites.value = await adminApi.deliverySites();
  if (sites.value.length === 0) {
    addSite();
  }
}

async function save() {
  saving.value = true;
  try {
    await adminApi.updateDeliverySites(sites.value.filter((site) => site.site_name));
    ElMessage.success("站点配置已保存");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>
