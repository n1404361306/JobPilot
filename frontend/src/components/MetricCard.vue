<template>
  <article class="metric-card" :class="`metric-card--${tone || 'blue'}`">
    <div class="metric-card__icon">
      <slot name="icon" />
    </div>
    <div>
      <p>{{ label }}</p>
      <strong>{{ value }}</strong>
      <span v-if="hint">{{ hint }}</span>
    </div>
  </article>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  hint?: string;
  tone?: "blue" | "green" | "amber" | "rose";
}>();
</script>
