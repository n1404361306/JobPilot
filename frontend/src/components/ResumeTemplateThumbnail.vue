<template>
  <div ref="viewportRef" class="resume-template-thumbnail">
    <div class="resume-template-thumbnail__stage" :style="stageStyle">
      <div class="resume-template-thumbnail__paper" :style="paperStyle">
        <ResumeStyledPreview
          compact
          :snapshot="snapshot"
          :template-id="templateId"
          :custom-template-content="customTemplateContent"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { ResumeFormSnapshot } from "@/composables/useResumeForm";
import ResumeStyledPreview from "@/components/ResumeStyledPreview.vue";
import type { ResumeTemplateId } from "@/utils/resumeTemplates";

const CANVAS_WIDTH = 820;

const props = withDefaults(
  defineProps<{
    snapshot: ResumeFormSnapshot;
    templateId: ResumeTemplateId;
    customTemplateContent?: string;
    height?: number;
  }>(),
  {
    height: 240
  }
);

const viewportRef = ref<HTMLElement>();
const scale = ref(0.5);
const contentHeight = ref(900);
const viewportHeight = computed(() => `${props.height}px`);

const stageStyle = computed(() => ({
  height: `${Math.ceil(contentHeight.value * scale.value)}px`
}));

const paperStyle = computed(() => ({
  width: `${CANVAS_WIDTH}px`,
  transform: `scale(${scale.value})`
}));

function measureContent() {
  const paper = viewportRef.value?.querySelector(".resume-template-thumbnail__paper .resume-doc") as HTMLElement | null;
  if (paper) {
    contentHeight.value = Math.max(paper.offsetHeight, 640);
  }
}

async function updateScale() {
  const viewport = viewportRef.value;
  if (!viewport) return;
  const available = Math.max(viewport.clientWidth - 16, 180);
  scale.value = Math.min(available / CANVAS_WIDTH, 1);
  await nextTick();
  measureContent();
}

let observer: ResizeObserver | null = null;

onMounted(() => {
  updateScale();
  observer = new ResizeObserver(() => {
    void updateScale();
  });
  if (viewportRef.value) {
    observer.observe(viewportRef.value);
  }
});

onBeforeUnmount(() => {
  observer?.disconnect();
});

watch(
  () => [props.templateId, props.customTemplateContent, props.snapshot] as const,
  () => {
    void updateScale();
  },
  { deep: true }
);
</script>

<style scoped>
.resume-template-thumbnail {
  height: v-bind(viewportHeight);
  overflow: hidden;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: linear-gradient(180deg, #eef2f7 0%, #f8fafc 100%);
  padding: 8px;
  box-sizing: border-box;
}

.resume-template-thumbnail__stage {
  width: 100%;
  overflow: hidden;
  display: flex;
  justify-content: center;
}

.resume-template-thumbnail__paper {
  transform-origin: top center;
  flex-shrink: 0;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.12);
  border-radius: 2px;
}

.resume-template-thumbnail__paper :deep(.resume-doc) {
  width: 820px;
  max-width: none;
  margin: 0;
  box-shadow: none;
}
</style>
