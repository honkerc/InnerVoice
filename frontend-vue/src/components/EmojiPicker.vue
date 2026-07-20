<template>
  <div ref="rootRef" class="emoji-picker" @mouseenter="openPanel" @mouseleave="scheduleClose">
    <div v-if="open" class="emoji-picker__panel-wrap" @mouseenter="openPanel" @mouseleave="scheduleClose">
      <div class="emoji-picker__panel">
        <button v-for="emoji in emojis" :key="emoji" type="button" class="emoji-picker__btn" @click="handlePick(emoji)">
          {{ emoji }}
        </button>
      </div>
    </div>
    <button type="button" class="toolbar-btn" :disabled="disabled" title="表情" @click="open = !open">
      <EmojiIcon />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { readEmojiList } from "@/lib/emoji-storage";

defineProps<{ disabled?: boolean }>();
const emit = defineEmits<{ pick: [emoji: string] }>();

const emojis = computed(() => readEmojiList());

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

function handlePick(emoji: string) {
  emit("pick", emoji);
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

<script lang="ts">
import { defineComponent, h } from "vue";

const EmojiIcon = defineComponent({
  setup() {
    return () =>
      h("svg", { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8" }, [
        h("circle", { cx: "12", cy: "12", r: "10" }),
        h("path", { d: "M8 14s1.5 2 4 2 4-2 4-2" }),
        h("line", { x1: "9", y1: "9", x2: "9.01", y2: "9" }),
        h("line", { x1: "15", y1: "9", x2: "15.01", y2: "9" }),
      ]);
  },
});

export default { components: { EmojiIcon } };
</script>
