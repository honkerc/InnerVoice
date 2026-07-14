<template>
  <div v-if="variant === 'answer'" ref="containerRef" class="ai-answer__plain">
    <MarkdownView :content="text" />
  </div>

  <div v-else ref="containerRef" :class="containerClass">
    <p v-if="waiting" class="ai-stream-line ai-stream-line--placeholder">正在分析问题…</p>
    <template v-for="(line, index) in lines" :key="index">
      <p v-if="line.trim()" class="ai-stream-line">{{ line }}</p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { splitDisplayLines, visibleStreamingLines } from "@/lib/stream-display";
import { useRevealingText } from "@/lib/useRevealingText";
import MarkdownView from "./MarkdownView.vue";

const props = defineProps<{
  text: string;
  streaming: boolean;
  variant: "thinking" | "answer";
}>();

const containerRef = ref<HTMLElement | null>(null);

const targetText = computed(() =>
  props.streaming ? visibleStreamingLines(props.text) : props.text,
);

const revealedText = useRevealingText(
  () => targetText.value,
  () => props.streaming && props.variant === "thinking",
);

const lines = computed(() => splitDisplayLines(revealedText.value));
const waiting = computed(
  () =>
    props.streaming &&
    props.variant === "thinking" &&
    lines.value.length === 0 &&
    revealedText.value.length === 0,
);

const containerClass = computed(() => "ai-thinking__body ai-stream-lines");

watch(
  () => [props.text, props.streaming, props.variant, lines.value.length] as const,
  () => {
    if (!props.streaming || !containerRef.value) return;
    containerRef.value.scrollTop = containerRef.value.scrollHeight;
  },
);
</script>
