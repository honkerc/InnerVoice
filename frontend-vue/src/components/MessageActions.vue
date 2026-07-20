<template>
  <div class="message-actions">
    <IconButton v-if="copyTextValue.trim()" :title="copied ? '已复制' : '复制'" @click="handleCopy">
      <IconCheck v-if="copied" />
      <IconCopy v-else />
    </IconButton>
    <IconButton v-if="canQuote" title="引用" @click="$emit('quote')">
      <IconQuote />
    </IconButton>
    <IconButton v-if="canEdit" title="编辑" @click="$emit('edit')">
      <IconEdit />
    </IconButton>
    <IconButton
      v-if="canPin"
      :title="isPinned ? '取消收藏' : '收藏'"
      :button-class="isPinned ? 'icon-btn--pin icon-btn--pin-active' : 'icon-btn--pin'"
      @click="$emit('pin')"
    >
      <IconPin :filled="isPinned" />
    </IconButton>
    <IconButton
      v-if="canDelete"
      :title="confirmingDelete ? '再次点击确认删除' : '删除'"
      :button-class="confirmingDelete ? 'icon-btn--delete icon-btn--delete-confirm' : 'icon-btn--delete'"
      @click="handleDelete"
    >
      <IconTrash />
    </IconButton>
  </div>
</template>

<script setup lang="ts">
import { onUnmounted, ref } from "vue";
import IconButton from "./IconButton.vue";
import { IconCheck, IconCopy, IconEdit, IconPin, IconQuote, IconTrash } from "./icons";
import { copyText } from "@/lib/copy-text";

const props = defineProps<{
  copyTextValue: string;
  canQuote?: boolean;
  canEdit?: boolean;
  canPin?: boolean;
  isPinned?: boolean;
  canDelete?: boolean;
}>();

const emit = defineEmits<{ quote: []; edit: []; pin: []; delete: [] }>();

const copied = ref(false);

async function handleCopy() {
  const ok = await copyText(props.copyTextValue);
  if (!ok) return;
  copied.value = true;
  window.setTimeout(() => {
    copied.value = false;
  }, 1500);
}

const confirmingDelete = ref(false);
let confirmTimer: ReturnType<typeof setTimeout> | null = null;

function handleDelete() {
  if (confirmingDelete.value) {
    if (confirmTimer) clearTimeout(confirmTimer);
    confirmingDelete.value = false;
    emit("delete");
    return;
  }
  confirmingDelete.value = true;
  confirmTimer = setTimeout(() => {
    confirmingDelete.value = false;
    confirmTimer = null;
  }, 3000);
}

onUnmounted(() => {
  if (confirmTimer) clearTimeout(confirmTimer);
});
</script>
