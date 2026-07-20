<template>
  <img v-if="type === 'image'" class="msg-image" :src="url" :alt="name || ''" @click="$emit('previewImage', url)" />
  <video v-else-if="type === 'video'" class="msg-video" :src="url" controls preload="metadata" />
  <a v-else class="msg-file-chip" :href="url" :download="name" target="_blank" rel="noopener">
    <IconFile :size="16" />
    <span class="msg-file-chip__name">{{ name || "文件" }}</span>
  </a>
</template>

<script setup lang="ts">
import type { AttachmentType } from "@/lib/types";
import { IconFile } from "./icons";

defineProps<{
  url: string;
  name?: string;
  type: AttachmentType;
}>();

defineEmits<{ previewImage: [url: string] }>();
</script>
