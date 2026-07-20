<template>
  <div v-if="tag" class="tag-filter-overlay" @click.self="$emit('close')">
    <div class="tag-filter-panel">
      <div class="tag-filter-panel__header">
        <span class="tag-filter-panel__title">#{{ tag }}</span>
        <IconButton title="关闭" @click="$emit('close')">
          <IconClose />
        </IconButton>
      </div>
      <div class="tag-filter-panel__body">
        <p v-if="loading" class="tag-filter-panel__empty">加载中…</p>
        <p v-else-if="!items.length" class="tag-filter-panel__empty">没有找到相关消息</p>
        <button v-for="item in items" :key="item.id" type="button" class="tag-filter-panel__item"
          @click="handleJump(item.id)">
          <span class="tag-filter-panel__text">{{ previewOf(item) }}</span>
          <span class="tag-filter-panel__date">{{ formatShortDate(item.createdAt) }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { fetchMessages } from "@/lib/api";
import { getMessageCopyText } from "@/lib/message-copy";
import { formatShortDate } from "@/lib/slash-command";
import { stripKnownTags } from "@/lib/tags";
import type { Message } from "@/lib/types";
import IconButton from "./IconButton.vue";
import { IconClose } from "./icons";

const props = defineProps<{ tag: string | null }>();
const emit = defineEmits<{ close: []; jump: [id: string] }>();

const items = ref<Message[]>([]);
const loading = ref(false);

function previewOf(message: Message): string {
  const text = stripKnownTags(getMessageCopyText(message), message.tags);
  if (text) return text.slice(0, 80);
  if (message.type === "image") return "[图片]";
  if (message.type === "video") return "[视频]";
  if (message.type === "file") return "[文件]";
  if (message.type === "media_group") return "[附件组]";
  return "";
}

function handleJump(id: string) {
  emit("jump", id);
}

watch(
  () => props.tag,
  async (tag) => {
    if (!tag) {
      items.value = [];
      return;
    }
    loading.value = true;
    try {
      const res = await fetchMessages({ tag, limit: 100 });
      items.value = res.items;
    } catch {
      items.value = [];
    } finally {
      loading.value = false;
    }
  },
  { immediate: true },
);
</script>
