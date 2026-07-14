<template>
  <AiMessageBlock v-if="visible && stream" :time-label="formatAiModelLabel(aiModelLabel)"
    :copy-text-value="getStreamCopyText(stream)" @preview-image="$emit('previewImage', $event)">
    <AiMessageContent :stream="stream" @preview-image="$emit('previewImage', $event)" />
  </AiMessageBlock>
</template>

<script setup lang="ts">
import type { AiStreamState } from "@/lib/ai-content";
import { formatAiModelLabel } from "@/lib/ai-label";
import { getStreamCopyText } from "@/lib/message-copy";
import AiMessageBlock from "./AiMessageBlock.vue";
import AiMessageContent from "./AiMessageContent.vue";

defineProps<{
  visible: boolean;
  stream: AiStreamState | null;
  aiModelLabel?: string;
}>();
</script>
