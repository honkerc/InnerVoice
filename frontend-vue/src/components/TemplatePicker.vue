<template>
  <div ref="rootRef" class="template-picker" @mouseenter="openPanel" @mouseleave="scheduleClose">
    <div v-if="open" class="template-picker__panel-wrap" @mouseenter="openPanel" @mouseleave="scheduleClose">
      <div class="template-picker__panel">
        <p v-if="!templates.length" class="template-picker__empty">还没有模板，去设置里添加</p>
        <button v-for="(tpl, i) in templates" :key="i" type="button" class="template-picker__item"
          :title="tpl.content" @click="handlePick(tpl)">
          {{ tpl.name || "未命名模板" }}
        </button>
      </div>
    </div>
    <button type="button" class="toolbar-btn" :disabled="disabled" title="插入模板" @click="open = !open">
      <IconTemplate />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { readTemplates, renderTemplate, type MessageTemplate } from "@/lib/template-storage";
import { IconTemplate } from "./icons";

defineProps<{ disabled?: boolean }>();
const emit = defineEmits<{ pick: [content: string] }>();

const templates = computed(() => readTemplates());

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

function handlePick(tpl: MessageTemplate) {
  emit("pick", renderTemplate(tpl.content));
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
