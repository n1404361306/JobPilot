import { createRouter, createWebHistory, type RouteLocationNormalized, type RouteRecordRaw } from "vue-router";
import { configureHttp } from "@/api/http";
import AppLayout from "@/layouts/AppLayout.vue";
import { useUserStore } from "@/stores/user";

export interface RouteAccessMeta {
  requiresAuth?: boolean;
  guestOnly?: boolean;
  adminOnly?: boolean;
  title?: string;
}

export type RouteAccessDecision = true | { name: string; query?: Record<string, string> };

export function decideRouteAccess(
  meta: RouteAccessMeta,
  isAuthenticated: boolean,
  redirect = "/",
  isAdmin = false
): RouteAccessDecision {
  if (meta.requiresAuth && !isAuthenticated) {
    return { name: "login", query: { redirect } };
  }

  if (meta.guestOnly && isAuthenticated) {
    return { name: "dashboard" };
  }

  if (meta.adminOnly && !isAdmin) {
    return { name: "dashboard" };
  }

  return true;
}

const pending = () => import("@/views/common/PendingView.vue");

export const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/auth/LoginView.vue"),
    meta: { guestOnly: true, title: "登录" }
  },
  {
    path: "/register",
    name: "register",
    component: () => import("@/views/auth/RegisterView.vue"),
    meta: { guestOnly: true, title: "注册" }
  },
  {
    path: "/",
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      { path: "", name: "dashboard", component: () => import("@/views/dashboard/DashboardView.vue"), meta: { title: "首页仪表盘" } },
      { path: "resumes/generate", name: "resume-generate", component: () => import("@/views/resumes/ResumeGenerateView.vue"), meta: { title: "文字生成简历" } },
      { path: "resumes/upload", name: "resume-upload", component: () => import("@/views/resumes/ResumeUploadView.vue"), meta: { title: "文件生成简历" } },
      { path: "resumes", name: "resume-list", component: () => import("@/views/resumes/ResumeListView.vue"), meta: { title: "简历列表" } },
      { path: "resumes/new", name: "resume-new", component: () => import("@/views/resumes/ResumeEditorView.vue"), meta: { title: "新建简历" } },
      { path: "resumes/:id/edit", name: "resume-edit", component: () => import("@/views/resumes/ResumeEditorView.vue"), meta: { title: "简历编辑器" } },
      { path: "resumes/:id/preview", name: "resume-preview", component: () => import("@/views/resumes/ResumePreviewView.vue"), meta: { title: "简历预览导出" } },
      { path: "templates", name: "template-gallery", component: () => import("@/views/resumes/TemplateGalleryView.vue"), meta: { title: "模板选择" } },
      {
        path: "templates/ai-maker",
        name: "template-ai-maker",
        component: () => import("@/views/resumes/AiTemplateMakerView.vue"),
        meta: { title: "AI 制作模板" }
      },
      { path: "jobs/import", name: "job-import", component: () => import("@/views/jobs/JobImportView.vue"), meta: { title: "岗位导入" } },
      { path: "jobs", name: "job-list", component: () => import("@/views/jobs/JobListView.vue"), meta: { title: "岗位列表" } },
      { path: "jobs/new", name: "job-new", component: () => import("@/views/jobs/JobDetailView.vue"), meta: { title: "新建岗位" } },
      { path: "jobs/:id", name: "job-detail", component: () => import("@/views/jobs/JobDetailView.vue"), meta: { title: "岗位详情" } },
      { path: "matching", name: "matching-report", component: () => import("@/views/matching/MatchingReportView.vue"), meta: { title: "匹配报告" } },
      { path: "optimization", name: "optimization", component: () => import("@/views/optimization/OptimizationView.vue"), meta: { title: "简历优化" } },
      { path: "interviews", name: "interviews", component: () => import("@/views/interviews/InterviewView.vue"), meta: { title: "模拟面试" } },
      { path: "delivery", name: "auto-delivery", component: () => import("@/views/delivery/AutoDeliveryView.vue"), meta: { title: "自动投递" } },
      { path: "applications", name: "application-board", component: () => import("@/views/applications/ApplicationBoardView.vue"), meta: { title: "投递看板" } },
      { path: "statistics", name: "statistics", component: () => import("@/views/statistics/StatisticsView.vue"), meta: { title: "数据统计" } },
      { path: "reports", name: "reports", component: () => import("@/views/reports/ReportsView.vue"), meta: { title: "AI 总结" } },
      { path: "admin/users", name: "admin-users", component: () => import("@/views/admin/AdminUsersView.vue"), meta: { title: "用户管理", adminOnly: true } },
      { path: "admin/templates", name: "admin-templates", component: () => import("@/views/admin/AdminTemplatesView.vue"), meta: { title: "模板管理", adminOnly: true } },
      { path: "admin/prompts", name: "admin-prompts", component: () => import("@/views/admin/AdminPromptsView.vue"), meta: { title: "Prompt 管理", adminOnly: true } },
      { path: "admin/ai-logs", name: "admin-ai-logs", component: () => import("@/views/admin/AdminAiLogsView.vue"), meta: { title: "AI 日志", adminOnly: true } },
      { path: "admin/ocr-logs", name: "admin-ocr-logs", component: () => import("@/views/admin/AdminOcrLogsView.vue"), meta: { title: "OCR 日志", adminOnly: true } },
      { path: "admin/delivery-sites", name: "admin-delivery-sites", component: () => import("@/views/admin/AdminDeliverySitesView.vue"), meta: { title: "投递站点配置", adminOnly: true } },
      { path: "admin/system-config", name: "admin-system-config", component: () => import("@/views/admin/AdminSystemConfigView.vue"), meta: { title: "系统配置", adminOnly: true } }
    ]
  },
  { path: "/:pathMatch(.*)*", name: "not-found", component: pending, meta: { title: "页面不存在" } }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

configureHttp({
  readToken: () => useUserStore().accessToken,
  onUnauthorized: () => {
    const userStore = useUserStore();
    userStore.clearSession();
    router.push({ name: "login" });
  }
});

router.beforeEach(async (to: RouteLocationNormalized) => {
  const userStore = useUserStore();

  if (userStore.isAuthenticated && !userStore.profile) {
    try {
      await userStore.fetchProfile();
    } catch {
      userStore.clearSession();
    }
  }

  return decideRouteAccess(
    to.meta as RouteAccessMeta,
    userStore.isAuthenticated,
    to.fullPath,
    userStore.isAdmin
  );
});

export default router;
