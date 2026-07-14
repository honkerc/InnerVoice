<template>
  <div v-if="items.length" class="image-preview-grid">
    <div v-for="item in items" :key="item.id" class="attachment-chip attachment-chip--image">
      <div class="attachment-chip__preview">
        <img :src="item.previewUrl" :alt="item.name" class="attachment-chip__img" />
        <div v-if="uploading" class="image-preview__overlay">
          <div class="image-preview__spinner" aria-hidden="true" />
        </div>
      </div>
      <button
        v-if="!uploading"
        type="button"
        class="attachment-chip__remove"
        aria-label="移除图片"
        @click="$emit('remove', item.id)"
      >
        <IconClose :size="12" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PendingImage } from "@/lib/pending-image";
import { IconClose } from "./icons";

defineProps<{ items: PendingImage[]; uploading?: boolean }>();
defineEmits<{ remove: [id: string] }>();
</script>
