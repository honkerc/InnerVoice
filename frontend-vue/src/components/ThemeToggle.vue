<template>
  <button type="button" class="theme-toggle" :title="isDark ? '切换到浅色' : '切换到深色'"
    :aria-label="isDark ? '切换到浅色' : '切换到深色'" @click="onToggle">
    <IconSun v-if="isDark" />
    <IconMoon v-else />
  </button>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { currentTheme, toggleTheme } from "@/lib/theme";
import { IconSun, IconMoon } from "./icons";

const isDark = ref(currentTheme() === "dark");

function onToggle() {
  isDark.value = toggleTheme() === "dark";
}
</script>
