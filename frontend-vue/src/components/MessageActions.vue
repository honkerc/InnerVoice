<template>
  <div class="message-actions">
    <IconButton v-if="copyTextValue.trim()" :title="copied ? '已复制' : '复制'" @click="handleCopy">
      <IconCheck v-if="copied" />
      <IconCopy v-else />
    </IconButton>
    <IconButton v-if="canQuote" title="引用" @click="$emit('quote')">
      <IconQuote />
    </IconButton>
    <IconButton
      v-if="canPin"
      :title="isPinned ? '取消置顶' : '置顶'"
      :button-class="isPinned ? 'icon-btn--pin icon-btn--pin-active' : 'icon-btn--pin'"
      @click="$emit('pin')"
    >
      <IconPin :filled="isPinned" />
    </IconButton>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import IconButton from "./IconButton.vue";
import { IconCheck, IconCopy, IconPin, IconQuote } from "./icons";
import { copyText } from "@/lib/copy-text";

const props = defineProps<{
  copyTextValue: string;
  canQuote?: boolean;
  canPin?: boolean;
  isPinned?: boolean;
}>();

defineEmits<{ quote: []; pin: [] }>();

const copied = ref(false);

async function handleCopy() {
  const ok = await copyText(props.copyTextValue);
  if (!ok) return;
  copied.value = true;
  window.setTimeout(() => {
    copied.value = false;
  }, 1500);
}
</script>
