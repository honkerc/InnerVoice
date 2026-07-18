<template>
  <div v-if="message" class="pinned-notice">
    <span class="pinned-notice__icon">📌</span>
    <span class="pinned-notice__text">{{ previewText }}</span>
    <button type="button" class="pinned-notice__close" title="取消置顶" @click.stop="$emit('unpin', message.id)">
      <IconClose :size="14" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Message } from "@/lib/types";
import { getMessageCopyText } from "@/lib/message-copy";
import { IconClose } from "./icons";

const props = defineProps<{ message: Message | null }>();

defineEmits<{
  jump: [id: string];
  unpin: [id: string];
}>();

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
</script>
