<template>
  <transition name="pinned-fade">
    <div v-if="items.length" ref="elRef" class="pinned-notice" :class="{ 'is-expanded': expanded }">
      <button type="button" class="pinned-notice__bar" @click="toggleExpand">
        <span class="pinned-notice__tag">收藏 {{ items.length }}</span>
        <span class="pinned-notice__preview">{{ previewText }}</span>
        <IconChevronDown class="pinned-notice__chevron" :size="16" />
      </button>
      <div class="pinned-notice__drawer">
        <div class="pinned-notice__drawer-inner">
          <div v-for="item in items" :key="item.id" class="favorites-bar__item">
            <button type="button" class="favorites-bar__item-body" title="点击定位原文" @click="handleJump(item.id)">
              {{ previewOf(item) }}
            </button>
            <button type="button" class="favorites-bar__item-remove" title="取消收藏" @click.stop="$emit('unfavorite', item.id)">
              <IconClose :size="12" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import type { Message } from "@/lib/types";
import { getMessageCopyText } from "@/lib/message-copy";
import { IconChevronDown, IconClose } from "./icons";

const props = defineProps<{ items: Message[] }>();

const emit = defineEmits<{
  jump: [id: string];
  unfavorite: [id: string];
}>();

const expanded = ref(false);
const elRef = ref<HTMLElement | null>(null);

watch(
  () => props.items.length,
  () => {
    if (!props.items.length) expanded.value = false;
  },
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
  if (!props.items.length) return;
  expanded.value = !expanded.value;
}

function handleJump(id: string) {
  expanded.value = false;
  emit("jump", id);
}

function previewOf(message: Message): string {
  const text = getMessageCopyText(message);
  if (text) return text;
  if (message.type === "image") return "[图片]";
  if (message.type === "media_group") return "[附件组]";
  if (message.type === "video") return "[视频]";
  if (message.type === "file") return "[文件]";
  return "收藏消息";
}

const previewText = computed(() => (props.items.length ? previewOf(props.items[0]) : ""));
</script>
