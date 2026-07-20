<template>
  <div ref="rootRef" class="template-picker" @mouseenter="openPanel" @mouseleave="scheduleClose">
    <div v-if="open" class="template-picker__panel-wrap" @mouseenter="openPanel" @mouseleave="scheduleClose">
      <div class="template-picker__panel">
        <button type="button" class="template-picker__item" @click="handlePick('week')">生成本周回顾</button>
        <button type="button" class="template-picker__item" @click="handlePick('month')">生成本月回顾</button>
      </div>
    </div>
    <button type="button" class="toolbar-btn" :disabled="disabled" title="AI 定期回顾" @click="open = !open">
      <IconRefresh />
    </button>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import type { AiReviewPeriod } from "@/lib/types";
import { IconRefresh } from "./icons";

defineProps<{ disabled?: boolean }>();
const emit = defineEmits<{ pick: [period: AiReviewPeriod] }>();

const open = ref(false);
const rootRef = ref<HTMLDivElement | null>(null);
let closeTimer: number | null = null;

function clearCloseTimer() {
  if (closeTimer !== null) {
    window.clearTimeout(closeTimer);
    closeTimer = null;
  }
}

function scheduleClose() {
  clearCloseTimer();
  closeTimer = window.setTimeout(() => {
    open.value = false;
  }, 180);
}

function openPanel() {
  if (closeTimer) clearCloseTimer();
  open.value = true;
}

function handlePick(period: AiReviewPeriod) {
  emit("pick", period);
  open.value = false;
}

function onPointerDown(event: MouseEvent) {
  if (rootRef.value && !rootRef.value.contains(event.target as Node)) {
    open.value = false;
  }
}

onMounted(() => {
  document.addEventListener("mousedown", onPointerDown);
});

onUnmounted(() => {
  clearCloseTimer();
  document.removeEventListener("mousedown", onPointerDown);
});
</script>
