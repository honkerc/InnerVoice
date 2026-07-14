<template>
  <IconButton
    v-if="visible"
    title="回到底部"
    button-class="scroll-to-bottom-btn"
    :style="{ bottom: `${bottomOffset + 12}px` }"
    @click="$emit('click')"
  >
    <IconChevronDown />
  </IconButton>
</template>

<script setup lang="ts">
import IconButton from "./IconButton.vue";
import { IconChevronDown } from "./icons";

defineProps<{
  visible: boolean;
  bottomOffset: number;
}>();

defineEmits<{ click: [] }>();
</script>
