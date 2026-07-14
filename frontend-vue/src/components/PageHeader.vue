<template>
  <header class="page-header">
    <div class="page-header__inner">
      <h1 v-if="title" class="page-header__title">{{ title }}</h1>
      <slot v-else name="left" />
      <div class="page-header__actions">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{ title?: string }>();
</script>
