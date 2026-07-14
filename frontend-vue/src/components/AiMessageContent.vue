<template>
  <div v-if="live" :class="['ai-message-content', { 'ai-message-content--answering': showAnswer }]">
    <section v-if="showThinking" :class="['ai-thinking', 'is-expanded', thinkingLive ? 'is-streaming' : 'is-done']">
      <div class="ai-thinking__head">
        <svg class="ai-thinking__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="1.8">
          <path d="M12 3a7 7 0 017 7c0 2.8-1.6 5.2-4 6.4V18a2 2 0 01-4 0v-1.6A7 7 0 0112 3z" />
          <path d="M9.5 21h5" />
        </svg>
        <span class="ai-thinking__label">{{ thinkingLabel }}</span>
        <span v-if="thinkingLive" class="ai-thinking__dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      </div>
      <div class="ai-thinking__body-wrap">
        <AiStreamText :text="stream!.thinking" :streaming="thinkingLive" variant="thinking" />
      </div>
    </section>
    <div v-if="showAnswer" :class="['ai-answer', { 'ai-answer--streaming': answerLive }]">
      <AiStreamText :text="stream!.answer" :streaming="answerLive" variant="answer" />
    </div>
  </div>

  <div v-else-if="hasContent" class="ai-message-content">
    <section v-if="parsed.thinking" class="ai-thinking is-expanded is-done">
      <div class="ai-thinking__head">
        <svg class="ai-thinking__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="1.8">
          <path d="M12 3a7 7 0 017 7c0 2.8-1.6 5.2-4 6.4V18a2 2 0 01-4 0v-1.6A7 7 0 0112 3z" />
          <path d="M9.5 21h5" />
        </svg>
        <span class="ai-thinking__label">已深度思考</span>
      </div>
      <div class="ai-thinking__body-wrap">
        <AiStreamText :text="parsed.thinking" :streaming="false" variant="thinking" />
      </div>
    </section>
    <div v-if="parsed.answer" class="ai-answer">
      <MarkdownView :content="parsed.answer" @preview-image="$emit('previewImage', $event)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { parseAiContent, type AiStreamState } from "@/lib/ai-content";
import { visibleStreamingLines } from "@/lib/stream-display";
import AiStreamText from "./AiStreamText.vue";
import MarkdownView from "./MarkdownView.vue";

const props = defineProps<{
  content?: string;
  stream?: AiStreamState | null;
}>();

const live = computed(() => !!props.stream);
const hasContent = computed(() => !!props.content?.trim());
const parsed = computed(() => parseAiContent(props.content ?? ""));

const thinkingLive = computed(() => props.stream?.phase === "thinking");
const answerLive = computed(() => props.stream?.phase === "answer");

const showThinking = computed(() => {
  if (!props.stream) return false;
  return thinkingLive.value || !!props.stream.thinking.trim();
});

const showAnswer = computed(() => {
  if (!props.stream) return false;
  const answerVisible = answerLive.value && !!visibleStreamingLines(props.stream.answer).trim();
  return answerVisible || (!answerLive.value && !!props.stream.answer.trim());
});

const thinkingLabel = computed(() => {
  if (!props.stream) return "";
  if (!thinkingLive.value) return "已深度思考";
  return props.stream.thinking.trim() ? "深度思考" : "思考中";
});

defineEmits<{
  previewImage: [url: string];
}>();
</script>
