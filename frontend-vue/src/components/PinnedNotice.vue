<template>
  <div ref="elRef" v-if="visible" class="pinned-notice" :class="{ 'pinned-notice--expanded': expanded }">
    <div class="pinned-notice__bar" @click="toggleExpand">
      <span class="pinned-notice__badge">备忘</span>
      <span class="pinned-notice__preview">{{ previewText }}</span>
      <button type="button" class="pinned-notice__close" title="隐藏公告" @click.stop="handleClose">
        <IconClose :size="14" />
      </button>
    </div>
    <div class="pinned-notice__drawer">
      <div class="pinned-notice__markdown markdown-body" v-html="markdownHtml" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import type { Message } from "@/lib/types";
import { getMessageCopyText } from "@/lib/message-copy";
import { parseAiContent } from "@/lib/ai-content";
import { isAiRole } from "@/lib/quote";
import { renderMarkdown } from "@/lib/markdown";
import { IconClose } from "./icons";

const props = defineProps<{ message: Message | null }>();

const emit = defineEmits<{
  jump: [id: string];
  unpin: [id: string];
}>();

const expanded = ref(false);
const visible = ref(true);
const elRef = ref<HTMLElement | null>(null);

// 每次 message 变化时重置状态
watch(
  () => props.message?.id,
  (id) => {
    if (!id) {
      visible.value = true;
      expanded.value = false;
      return;
    }
    const hidden = localStorage.getItem(`pinned-hidden:${id}`);
    visible.value = hidden !== "1";
    expanded.value = false;
  },
  { immediate: true },
);

function onClickOutside(e: MouseEvent) {
  if (!expanded.value) return;
  if (elRef.value && !elRef.value.contains(e.target as Node)) {
    expanded.value = false;
  }
}

onMounted(() => {
  document.addEventListener("click", onClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", onClickOutside);
});

function toggleExpand() {
  if (!props.message) return;
  expanded.value = !expanded.value;
}

function handleClose() {
  if (!props.message) return;
  localStorage.setItem(`pinned-hidden:${props.message.id}`, "1");
  visible.value = false;
}

const previewText = computed(() => {
  if (!props.message) return "";
  const text = getMessageCopyText(props.message);
  if (text) return text;
  if (props.message.type === "image") return "[图片]";
  if (props.message.type === "media_group") return "[附件组]";
  if (props.message.type === "video") return "[视频]";
  if (props.message.type === "file") return "[文件]";
  return "置顶消息";
});

const markdownHtml = computed(() => {
  if (!props.message) return "";
  let content = props.message.content;
  if (props.message.type === "text" && isAiRole(props.message.role)) {
    const { answer, thinking } = parseAiContent(content);
    content = answer || thinking;
  }
  return renderMarkdown(content);
});
</script>
