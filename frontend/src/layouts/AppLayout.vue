<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <RouterLink class="brand" :to="{ name: 'dashboard' }">
        <span class="brand__mark">J</span>
        <span>JobPilot</span>
      </RouterLink>
      <el-scrollbar class="sidebar-scroll">
        <el-menu :default-active="route.path" router class="side-menu">
          <template v-for="group in visibleGroups" :key="group.title">
            <div class="menu-group-title">{{ group.title }}</div>
            <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>
    </aside>

    <section class="app-main">
      <header class="topbar">
        <div class="topbar__left">
          <el-button class="mobile-menu-button" :icon="Menu" circle @click="drawerVisible = true" />
          <div>
            <p>{{ route.meta.title || "JobPilot" }}</p>
            <span>{{ userStore.profile?.username || "求职者" }}</span>
          </div>
        </div>
        <el-dropdown>
          <el-button>
            {{ userStore.profile?.username || "账号" }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push({ name: 'dashboard' })">首页</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </section>

    <el-drawer v-model="drawerVisible" direction="ltr" size="280px" title="JobPilot">
      <el-menu :default-active="route.path" router @select="drawerVisible = false">
        <template v-for="group in visibleGroups" :key="group.title">
          <div class="menu-group-title">{{ group.title }}</div>
          <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowDown,
  Briefcase,
  Collection,
  DataAnalysis,
  Document,
  EditPen,
  Files,
  Histogram,
  House,
  MagicStick,
  Management,
  Menu,
  Monitor,
  Promotion,
  Reading,
  Setting,
  Upload,
  User
} from "@element-plus/icons-vue";
import { computed, ref } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const drawerVisible = ref(false);

const menuGroups = [
  {
    title: "求职工作台",
    items: [
      { label: "首页仪表盘", path: "/", icon: House },
      { label: "文字生成简历", path: "/resumes/generate", icon: MagicStick },
      { label: "文件生成简历", path: "/resumes/upload", icon: Upload },
      { label: "简历列表", path: "/resumes", icon: Files },
      { label: "模板选择", path: "/templates", icon: Collection },
      { label: "岗位导入", path: "/jobs/import", icon: Promotion },
      { label: "岗位列表", path: "/jobs", icon: Briefcase },
      { label: "匹配报告", path: "/matching", icon: DataAnalysis },
      { label: "简历优化", path: "/optimization", icon: EditPen },
      { label: "模拟面试", path: "/interviews", icon: Monitor },
      { label: "投递看板", path: "/applications", icon: Management },
      { label: "数据统计", path: "/statistics", icon: Histogram },
      { label: "AI 总结", path: "/reports", icon: Reading }
    ]
  },
  {
    title: "管理员",
    admin: true,
    items: [
      { label: "用户管理", path: "/admin/users", icon: User },
      { label: "模板管理", path: "/admin/templates", icon: Document },
      { label: "Prompt 管理", path: "/admin/prompts", icon: EditPen },
      { label: "AI 日志", path: "/admin/ai-logs", icon: DataAnalysis },
      { label: "OCR 日志", path: "/admin/ocr-logs", icon: Reading },
      { label: "站点配置", path: "/admin/delivery-sites", icon: Setting },
      { label: "系统配置", path: "/admin/system-config", icon: Setting }
    ]
  }
];

const visibleGroups = computed(() => menuGroups.filter((group) => !group.admin || userStore.isAdmin));

async function handleLogout() {
  await userStore.logout();
  router.push({ name: "login" });
}
</script>
