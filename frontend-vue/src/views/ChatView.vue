<template>
  <div class="chat-page" :style="{ '--chat-editor-height': `${editorHeight}px` }">
    <main ref="mainRef" class="page-main" :style="{ paddingBottom: `${editorHeight}px` }">
      <PinnedNotice :message="pinnedMessage" @jump="jumpToMessage" @unpin="togglePin" />
      <ChatSkeleton v-if="loading" />
      <div v-else class="chat-feed">
        <MessageRow v-for="message in messages" :key="message.id" :message="message"
          :pinned="settings?.pinnedMessageId === message.id" :highlighted="highlightedMessageId === message.id"
          :can-quote="!quotedIds.has(message.id) && quote?.id !== message.id" :user-avatar="settings?.avatarUrl"
          :user-name="settings?.displayName" :ai-model-label="settings?.aiModel" @quote="setQuote" @pin="togglePin"
          @jump-quote="jumpToMessage" @preview-image="lightboxUrl = $event" />
        <StreamAiRow :visible="streaming" :stream="streamState" :ai-model-label="settings?.aiModel"
          @preview-image="lightboxUrl = $event" />
        <div ref="bottomRef" class="chat-scroll-anchor" :style="{ scrollMarginBottom: `${editorHeight}px` }"
          aria-hidden="true" />
      </div>
    </main>

    <ScrollToBottomButton :visible="!loading && !atBottom" :bottom-offset="editorHeight"
      @click="handleScrollToBottom" />

    <ChatEditor :layout-width="980" :quoting-message="quote" @clear-quote="quote = null" @sent="handleSent"
      @error="error = $event" @ai-stream-start="startStream" @ai-stream-update="updateStream"
      @ai-stream-done="finishStream" @ai-stream-clear="clearStream" @zone-height-change="editorHeight = $event" />

    <div v-if="error" class="toast" @click="error = ''">{{ error }}</div>

    <div v-if="lightboxUrl" class="lightbox" @click="lightboxUrl = ''">
      <button type="button" @click.stop="lightboxUrl = ''">×</button>
      <img :src="lightboxUrl" alt="" @click.stop />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { fetchMessages, fetchSettings, pinMessage } from "@/lib/api";
import type { Message } from "@/lib/types";
import type { UserSettings } from "@/lib/settings-types";
import type { AiStreamState } from "@/lib/ai-content";
import { getQuotedMessageIds } from "@/lib/quote";
import { scrollToMessage } from "@/lib/scroll-to-message";
import MessageRow from "@/components/MessageRow.vue";
import StreamAiRow from "@/components/StreamAiRow.vue";
import ChatEditor from "@/components/ChatEditor.vue";
import ScrollToBottomButton from "@/components/ScrollToBottomButton.vue";
import ChatSkeleton from "@/components/ChatSkeleton.vue";
import PinnedNotice from "@/components/PinnedNotice.vue";

const MESSAGE_HIGHLIGHT_MS = 2800;
const BOTTOM_THRESHOLD = 160;

const loading = ref(true);
const error = ref("");
const messages = ref<Message[]>([]);
const settings = ref<UserSettings | null>(null);
const quote = ref<Message | null>(null);
const editorHeight = ref(220);
const lightboxUrl = ref("");
const streaming = ref(false);
const streamThinking = ref("");
const streamAnswer = ref("");
const streamPhase = ref<"thinking" | "answer">("thinking");
const highlightedMessageId = ref<string | null>(null);
const atBottom = ref(true);
const mainRef = ref<HTMLElement | null>(null);
const bottomRef = ref<HTMLElement | null>(null);
const stickToBottom = ref(true);
const scrollAfterSend = ref(false);
let highlightTimer: ReturnType<typeof setTimeout> | null = null;
let resizeFrame = 0;
let streamScrollFrame = 0;

const pinnedMessage = computed(() => {
  const id = settings.value?.pinnedMessageId;
  if (!id) return null;
  return messages.value.find((m) => m.id === id) ?? null;
});

const quotedIds = computed(() => getQuotedMessageIds(messages.value));
const streamState = computed<AiStreamState | null>(() => {
  if (!streaming.value) return null;
  return {
    thinking: streamThinking.value,
    answer: streamAnswer.value,
    phase: streamPhase.value,
  };
});

function syncAtBottom() {
  const el = document.documentElement;
  const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_THRESHOLD + editorHeight.value * 0.15;
  stickToBottom.value = nearBottom;
  atBottom.value = nearBottom;
}

function onWindowScroll() {
  syncAtBottom();
}

async function scrollToLatest(behavior: ScrollBehavior = "smooth", force = false) {
  if (!force && !stickToBottom.value && !streaming.value) return;
  await nextTick();
  const anchor = bottomRef.value;
  if (anchor) {
    anchor.scrollIntoView({ block: "end", behavior });
  } else {
    const doc = document.documentElement;
    const top = doc.scrollHeight - window.innerHeight;
    window.scrollTo({ top: Math.max(0, top), behavior });
  }
}

function scheduleStreamScroll() {
  cancelAnimationFrame(streamScrollFrame);
  streamScrollFrame = requestAnimationFrame(() => {
    void scrollToLatest("auto", true);
  });
}

onMounted(async () => {
  window.addEventListener("scroll", onWindowScroll, { passive: true });
  syncAtBottom();

  try {
    const [list, cfg] = await Promise.all([fetchMessages(), fetchSettings()]);
    messages.value = list;
    settings.value = cfg;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载失败";
  } finally {
    loading.value = false;
    stickToBottom.value = true;
    await scrollToLatest("auto", true);
  }
});

onUnmounted(() => {
  window.removeEventListener("scroll", onWindowScroll);
  if (highlightTimer) clearTimeout(highlightTimer);
  cancelAnimationFrame(resizeFrame);
  cancelAnimationFrame(streamScrollFrame);
});

watch(streaming, (active) => {
  if (active) {
    stickToBottom.value = true;
    atBottom.value = true;
    scheduleStreamScroll();
  }
});

watch(
  () => messages.value.length,
  () => {
    if (!scrollAfterSend.value) return;
    scrollAfterSend.value = false;
    void scrollToLatest("smooth", true);
  },
);

watch(
  () => [streamThinking.value, streamAnswer.value, streamPhase.value] as const,
  () => {
    if (streaming.value) scheduleStreamScroll();
  },
);

watch(editorHeight, () => {
  if (stickToBottom.value || streaming.value) {
    void scrollToLatest("auto", true);
  }
});

watch(
  () => mainRef.value,
  (main, _prev, onCleanup) => {
    if (!main) return;

    const observer = new ResizeObserver(() => {
      if (!stickToBottom.value && !streaming.value) return;
      cancelAnimationFrame(resizeFrame);
      resizeFrame = requestAnimationFrame(() => {
        void scrollToLatest(streaming.value ? "auto" : "smooth", true);
      });
    });

    observer.observe(main);
    onCleanup(() => {
      cancelAnimationFrame(resizeFrame);
      observer.disconnect();
    });
  },
  { immediate: true },
);

function handleScrollToBottom() {
  stickToBottom.value = true;
  atBottom.value = true;
  void scrollToLatest("smooth", true);
}

function setQuote(message: Message) {
  quote.value = message;
}

async function togglePin(id: string) {
  try {
    const nextId = settings.value?.pinnedMessageId === id ? null : id;
    settings.value = await pinMessage(nextId);
  } catch {
    error.value = "置顶失败";
  }
}

function jumpToMessage(id: string) {
  scrollToMessage(id);
  if (highlightTimer) clearTimeout(highlightTimer);
  highlightedMessageId.value = id;
  highlightTimer = setTimeout(() => {
    highlightedMessageId.value = null;
    highlightTimer = null;
  }, MESSAGE_HIGHLIGHT_MS);
}

function handleSent(message: Message) {
  scrollAfterSend.value = true;
  stickToBottom.value = true;
  atBottom.value = true;
  messages.value.push(message);
  error.value = "";
  void scrollToLatest("smooth", true);
}

function startStream() {
  streaming.value = true;
  streamThinking.value = "";
  streamAnswer.value = "";
  streamPhase.value = "thinking";
  stickToBottom.value = true;
  atBottom.value = true;
  scheduleStreamScroll();
}

function updateStream(state: AiStreamState) {
  streamThinking.value = state.thinking;
  streamAnswer.value = state.answer;
  streamPhase.value = state.phase;
  scheduleStreamScroll();
}

function finishStream(message: Message) {
  streaming.value = false;
  streamThinking.value = "";
  streamAnswer.value = "";
  streamPhase.value = "thinking";
  if (!messages.value.some((m) => m.id === message.id)) {
    messages.value.push(message);
  }
  stickToBottom.value = true;
  void scrollToLatest("smooth", true);
}

function clearStream() {
  streaming.value = false;
  streamThinking.value = "";
  streamAnswer.value = "";
  streamPhase.value = "thinking";
}
</script>
