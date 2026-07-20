<template>
  <div v-if="items.length" class="image-preview-grid">
    <div
      v-for="item in items"
      :key="item.id"
      :class="['attachment-chip', `attachment-chip--${item.kind}`]"
    >
      <div class="attachment-chip__preview">
        <img v-if="item.kind === 'image'" :src="item.previewUrl" :alt="item.name" class="attachment-chip__img" />
        <video v-else-if="item.kind === 'video'" :src="item.previewUrl" class="attachment-chip__img" muted />
        <div v-else class="attachment-chip__file">
          <IconFile :size="20" />
          <span class="attachment-chip__filename">{{ item.name }}</span>
        </div>
        <div v-if="uploading" class="image-preview__overlay">
          <div class="image-preview__spinner" aria-hidden="true" />
        </div>
      </div>
      <button
        v-if="!uploading"
        type="button"
        class="attachment-chip__remove"
        aria-label="移除附件"
        @click="$emit('remove', item.id)"
      >
        <IconClose :size="12" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PendingMedia } from "@/lib/pending-media";
import { IconClose, IconFile } from "./icons";

defineProps<{ items: PendingMedia[]; uploading?: boolean }>();
defineEmits<{ remove: [id: string] }>();
</script>
