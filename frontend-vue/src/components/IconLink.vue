<template>
  <RouterLink :to="to" class="icon-btn" :class="linkClass" :title="title" :aria-label="title">
    <slot />
  </RouterLink>
</template>

<script setup lang="ts">
defineProps<{
  to: string;
  title: string;
  linkClass?: string;
}>();
</script>
