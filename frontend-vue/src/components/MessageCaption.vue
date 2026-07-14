<template>
  <MarkdownView v-if="content.trim()" :content="content" />
</template>

<script setup lang="ts">
import MarkdownView from "./MarkdownView.vue";

defineProps<{ content: string }>();
</script>
