<template>
  <div :class="['quote-inline', { 'quote-inline--compact': compact }]">
    <button
      v-if="clickable"
      type="button"
      class="quote-inline__link"
      title="跳转到原消息"
      aria-label="跳转到原消息"
      @click="$emit('jump')"
    >
      <QuoteBody :quote="quote" />
    </button>
    <div v-else class="quote-inline__static">
      <QuoteBody :quote="quote" />
    </div>
    <IconButton
      v-if="showClose"
      title="取消引用"
      button-class="quote-inline__close"
      @click="$emit('close')"
    >
      <IconClose />
    </IconButton>
  </div>
</template>

<script setup lang="ts">
import type { QuotePreview } from "@/lib/types";
import IconButton from "./IconButton.vue";
import { IconClose } from "./icons";
import QuoteBody from "./QuoteBody.vue";

defineProps<{
  quote: QuotePreview;
  compact?: boolean;
  clickable?: boolean;
  showClose?: boolean;
}>();

defineEmits<{ jump: []; close: [] }>();
</script>
