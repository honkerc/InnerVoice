<template>
  <div v-if="message" class="pinned-notice" role="status">
    <div class="pinned-notice__inner">
      <div class="pinned-notice__header">
        <span class="pinned-notice__badge">📌 公告</span>
        <span class="pinned-notice__meta">
          <template v-if="authorName">{{ authorName }} · </template>
          {{ timeAgo }}
        </span>
        <button type="button" class="pinned-notice__close" title="取消置顶" aria-label="取消置顶"
          @click.stop="$emit('unpin', message.id)">
          <IconClose :size="14" />
        </button>
      </div>
      <button type="button" class="pinned-notice__body" @click="$emit('jump', message.id)">
        <p class="pinned-notice__text">{{ previewText }}</p>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Message } from "@/lib/types";
import { getMessageCopyText } from "@/lib/message-copy";
import { isAiRole } from "@/lib/quote";
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

const authorName = computed(() => {
  if (!props.message) return "";
  if (isAiRole(props.message.role)) return "AI";
  return props.message.authorDisplayName || "";
});

const timeAgo = computed(() => {
  if (!props.message) return "";
  const date = new Date(props.message.createdAt);
  const now = Date.now();
  const diff = now - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;
  if (hours < 24) return `${hours} 小时前`;
  if (days < 30) return `${days} 天前`;
  return date.toLocaleDateString("zh-CN");
});
</script>
