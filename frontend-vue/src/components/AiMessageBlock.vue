<template>
  <section class="ai-message-block" :class="{ 'is-highlighted': highlighted }"
    :id="messageId ? `message-${messageId}` : undefined">
    <div class="ai-message-block__meta">
      <span v-if="timeLabel" class="ai-message-block__label">{{ timeLabel }}</span>
    </div>
    <div class="ai-message-block__body">
      <QuotePreview v-if="quote" :quote="quote" @jump="$emit('jumpQuote', quote!.id)" />
      <slot />
    </div>
    <div class="ai-message-block__actions">
      <div class="message-actions-wrap" :class="{ 'message-actions-wrap--pinned': isPinned }">
        <MessageActions :copy-text-value="copyTextValue" :can-quote="canQuote" :can-pin="canPin" :is-pinned="isPinned"
          @quote="$emit('quote')" @pin="$emit('pin')" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Message } from "@/lib/types";
import QuotePreview from "./QuotePreview.vue";
import MessageActions from "./MessageActions.vue";

defineProps<{
  messageId?: string;
  timeLabel: string;
  copyTextValue: string;
  canQuote?: boolean;
  canPin?: boolean;
  isPinned?: boolean;
  highlighted?: boolean;
  quote?: Message["quote"];
}>();

defineEmits<{
  quote: [];
  pin: [];
  jumpQuote: [id: string];
  previewImage: [url: string];
}>();
</script>
