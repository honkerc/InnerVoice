<template>
  <button
    type="button"
    class="icon-btn"
    :class="buttonClass"
    :title="title"
    :aria-label="title"
    :style="style"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import type { CSSProperties } from "vue";

defineProps<{
  title: string;
  buttonClass?: string;
  style?: CSSProperties;
}>();

defineEmits<{ click: [event: MouseEvent] }>();
</script>
