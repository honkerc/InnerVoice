<template>
  <div v-if="tags?.length" class="tag-chips">
    <button v-for="tag in tags" :key="tag" type="button" class="tag-chip" @click="$emit('select', tag)">
      #{{ tag }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ tags?: string[] | null }>();
defineEmits<{ select: [tag: string] }>();
</script>
