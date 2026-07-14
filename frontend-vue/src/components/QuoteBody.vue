<template>
  <div class="quote-inline__icon" aria-hidden="true">
    <IconQuote :size="14" />
  </div>
  <div class="quote-inline__bar" aria-hidden="true" />
  <div class="quote-inline__body">
    <p class="quote-inline__text">{{ summary }}</p>
    <img v-if="hasThumb" :src="quote.mediaUrl!" alt="" class="quote-inline__thumb" />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { QuotePreview } from "@/lib/types";
import { getQuoteSummary } from "@/lib/quote";
import { IconQuote } from "./icons";

const props = defineProps<{ quote: QuotePreview }>();

function typeHint(type: QuotePreview["type"], content: string) {
  if (type === "media_group" && !content) return "附件组";
  if (type === "image" && !content) return "图片";
  if (type === "video" && !content) return "视频";
  if (type === "file" && !content) return "附件";
  return null;
}

const summary = computed(() => typeHint(props.quote.type, props.quote.content) || getQuoteSummary(props.quote));
const hasThumb = computed(() => props.quote.type === "image" && props.quote.mediaUrl);
</script>
