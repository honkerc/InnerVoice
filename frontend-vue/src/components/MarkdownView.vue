<template>
  <div v-if="html" class="markdown-body" v-html="html" @click="onClick" />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { renderMarkdown } from "@/lib/markdown";

const props = defineProps<{ content: string }>();
const html = computed(() => (props.content.trim() ? renderMarkdown(props.content) : ""));

const emit = defineEmits<{
  previewImage: [url: string];
}>();

function onClick(e: MouseEvent) {
  const target = e.target as HTMLElement;
  if (target.tagName === "IMG") {
    const src = (target as HTMLImageElement).src;
    if (src) emit("previewImage", src);
  }
}
</script>
