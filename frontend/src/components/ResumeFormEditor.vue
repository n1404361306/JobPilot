<template>
  <el-tabs v-model="activeTab" class="editor-tabs">
    <el-tab-pane label="基本信息" name="basic">
      <el-form label-position="top">
        <ResumePhotoUpload v-model="resumeForm.basic_info.photo" />
        <div class="form-grid">
          <el-form-item label="姓名"><el-input v-model="resumeForm.basic_info.name" /></el-form-item>
          <el-form-item label="电话"><el-input v-model="resumeForm.basic_info.phone" /></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="resumeForm.basic_info.email" /></el-form-item>
          <el-form-item label="GitHub"><el-input v-model="resumeForm.basic_info.github" /></el-form-item>
          <el-form-item label="个人网站"><el-input v-model="resumeForm.basic_info.website" /></el-form-item>
          <el-form-item label="所在地"><el-input v-model="resumeForm.basic_info.location" /></el-form-item>
        </div>
        <el-form-item label="求职意向"><el-input v-model="resumeForm.job_intention" /></el-form-item>
        <el-form-item label="个人简介"><el-input v-model="resumeForm.summary" type="textarea" :rows="4" /></el-form-item>
      </el-form>
    </el-tab-pane>

    <el-tab-pane label="技能" name="skills">
      <el-form label-position="top">
        <el-form-item label="编程语言"><el-input v-model="skillsText.languages" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="后端开发"><el-input v-model="skillsText.backend" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="数据库与中间件"><el-input v-model="skillsText.database" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="AI / 算法"><el-input v-model="skillsText.ai" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="工程工具"><el-input v-model="skillsText.tools" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="语言能力"><el-input v-model="skillsText.language_ability" type="textarea" :rows="2" /></el-form-item>
      </el-form>
    </el-tab-pane>

    <el-tab-pane label="教育" name="education">
      <div class="section-actions">
        <el-button type="primary" link @click="addEducation">添加教育经历</el-button>
      </div>
      <article v-for="(item, index) in resumeForm.education" :key="index" class="sub-card">
        <div class="sub-card-header">
          <span>教育经历 {{ index + 1 }}</span>
          <el-button v-if="resumeForm.education.length > 1" type="danger" link @click="removeEducation(index)">删除</el-button>
        </div>
        <el-form label-position="top">
          <div class="form-grid">
            <el-form-item label="学校"><el-input v-model="item.school" /></el-form-item>
            <el-form-item label="专业"><el-input v-model="item.major" /></el-form-item>
            <el-form-item label="学历"><el-input v-model="item.degree" /></el-form-item>
            <el-form-item label="时间"><el-input v-model="item.period" /></el-form-item>
          </div>
          <el-form-item label="研究方向"><el-input v-model="item.research_direction" /></el-form-item>
          <el-form-item label="GPA"><el-input v-model="item.gpa" /></el-form-item>
          <el-form-item label="课程/荣誉"><el-input v-model="item.highlightsText" type="textarea" :rows="3" /></el-form-item>
        </el-form>
      </article>
    </el-tab-pane>

    <el-tab-pane label="实习" name="internships">
      <div class="section-actions">
        <el-button type="primary" link @click="addInternship">添加实习经历</el-button>
      </div>
      <article v-for="(item, index) in resumeForm.internships" :key="index" class="sub-card">
        <div class="sub-card-header">
          <span>实习经历 {{ index + 1 }}</span>
          <el-button v-if="resumeForm.internships.length > 1" type="danger" link @click="removeInternship(index)">删除</el-button>
        </div>
        <el-form label-position="top">
          <div class="form-grid">
            <el-form-item label="公司"><el-input v-model="item.company" /></el-form-item>
            <el-form-item label="职位"><el-input v-model="item.position" /></el-form-item>
            <el-form-item label="时间"><el-input v-model="item.period" /></el-form-item>
            <el-form-item label="地点"><el-input v-model="item.location" /></el-form-item>
          </div>
          <el-form-item label="工作概述"><el-input v-model="item.description" type="textarea" :rows="3" /></el-form-item>
          <el-form-item label="主要工作"><el-input v-model="item.responsibilitiesText" type="textarea" :rows="5" /></el-form-item>
          <el-form-item label="技术栈"><el-input v-model="item.techStackText" /></el-form-item>
        </el-form>
      </article>
    </el-tab-pane>

    <el-tab-pane label="项目" name="projects">
      <div class="section-actions">
        <el-button type="primary" link @click="addProject">添加项目经历</el-button>
      </div>
      <article v-for="(item, index) in resumeForm.projects" :key="index" class="sub-card">
        <div class="sub-card-header">
          <span>项目经历 {{ index + 1 }}</span>
          <el-button v-if="resumeForm.projects.length > 1" type="danger" link @click="removeProject(index)">删除</el-button>
        </div>
        <el-form label-position="top">
          <div class="form-grid">
            <el-form-item label="项目名称"><el-input v-model="item.project_name" /></el-form-item>
            <el-form-item label="项目类型"><el-input v-model="item.type" /></el-form-item>
            <el-form-item label="时间"><el-input v-model="item.period" /></el-form-item>
          </div>
          <el-form-item label="项目概述"><el-input v-model="item.description" type="textarea" :rows="3" /></el-form-item>
          <el-form-item label="主要职责"><el-input v-model="item.responsibilitiesText" type="textarea" :rows="5" /></el-form-item>
          <el-form-item label="技术栈"><el-input v-model="item.techStackText" /></el-form-item>
          <el-form-item label="项目成果"><el-input v-model="item.resultsText" type="textarea" :rows="4" /></el-form-item>
        </el-form>
      </article>
    </el-tab-pane>

    <el-tab-pane label="其他" name="other">
      <el-form label-position="top">
        <el-form-item label="科研经历"><el-input v-model="researchText" type="textarea" :rows="5" /></el-form-item>
        <el-form-item label="获奖经历"><el-input v-model="awardsText" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="证书"><el-input v-model="certificatesText" /></el-form-item>
        <el-form-item label="开源贡献"><el-input v-model="resumeForm.open_source" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="兴趣方向"><el-input v-model="resumeForm.interests" /></el-form-item>
        <el-form-item label="个人评价"><el-input v-model="resumeForm.self_evaluation" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="待补充内容"><el-input v-model="missingText" type="textarea" :rows="3" /></el-form-item>
      </el-form>
    </el-tab-pane>
  </el-tabs>
</template>

<script setup lang="ts">
import type { useResumeForm } from "@/composables/useResumeForm";
import ResumePhotoUpload from "@/components/ResumePhotoUpload.vue";

const activeTab = defineModel<string>("activeTab", { default: "basic" });

const props = defineProps<{
  formApi: ReturnType<typeof useResumeForm>;
}>();

const {
  resumeForm,
  skillsText,
  researchText,
  awardsText,
  certificatesText,
  missingText,
  addEducation,
  removeEducation,
  addInternship,
  removeInternship,
  addProject,
  removeProject
} = props.formApi;
</script>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.sub-card {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 14px;
}

.sub-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-weight: 600;
}

.section-actions {
  margin-bottom: 12px;
}

@media (max-width: 760px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
