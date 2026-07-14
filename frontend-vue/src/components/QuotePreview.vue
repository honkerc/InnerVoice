<template>
  <div class="quote-preview" @click="$emit('jump')">
    <div class="hint">引用</div>
    <div>{{ preview }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { QuotePreview } from "@/lib/types";
import { getQuoteSummary } from "@/lib/quote";

const props = defineProps<{ quote: QuotePreview }>();
defineEmits<{ jump: [] }>();

const preview = computed(() => getQuoteSummary(props.quote));
</script>
