<template>
  <div class="chat-page" :style="{ '--chat-editor-height': `${editorHeight}px` }">
    <div class="chat-top-cover" aria-hidden="true" />
    <FavoritesBar :items="favorites" @jump="jumpToMessage" @unfavorite="toggleFavorite" />

    <main ref="mainRef" class="page-main" :style="{ paddingBottom: `${editorHeight}px` }">
      <ChatSkeleton v-if="loading" />
      <div v-else class="chat-feed">
        <div v-if="!messages.length && !streaming" class="chat-empty">
          <p class="chat-empty__title">开始与自己对话</p>
          <p class="chat-empty__desc">写下此刻的想法、问题或日精进；输入 @ai 可让另一个声音回应你。</p>
        </div>
        <div v-if="hasMoreBefore || loadingOlder" class="chat-load-more" aria-hidden="true">
          {{ loadingOlder ? "加载更早…" : "上滑加载更早" }}
        </div>
        <MessageRow v-for="message in messages" :key="message.id" :message="message"
          :pinned="favorites.some((f) => f.id === message.id)" :highlighted="highlightedMessageId === message.id"
          :can-quote="!quotedIds.has(message.id) && quote?.id !== message.id" :user-avatar="settings?.avatarUrl"
          :user-name="settings?.displayName" :ai-model-label="settings?.aiModel" @quote="setQuote"
          @pin="toggleFavorite" @delete="handleDelete" @jump-quote="jumpToMessage"
          @preview-image="lightboxUrl = $event" @edited="handleEdited" @filter-tag="filterTag = $event" />
        <StreamAiRow :visible="streaming" :stream="streamState" :ai-model-label="settings?.aiModel"
          @preview-image="lightboxUrl = $event" />
        <div ref="bottomRef" class="chat-scroll-anchor" :style="{ scrollMarginBottom: `${editorHeight}px` }"
          aria-hidden="true" />
      </div>
    </main>

    <ScrollToBottomButton :visible="!loading && !atBottom" :bottom-offset="editorHeight"
      @click="handleScrollToBottom" />

    <ChatEditor :layout-width="980" :quoting-message="quote" @clear-quote="quote = null" @sent="handleSent"
      @error="error = $event" @jump="jumpToMessage" @jump-date="handleJumpDate" @ai-stream-start="startStream"
      @ai-stream-update="updateStream" @ai-stream-done="finishStream" @ai-stream-clear="clearStream"
      @zone-height-change="editorHeight = $event" />

    <div v-if="error" class="toast" @click="error = ''">{{ error }}</div>

    <div v-if="lightboxUrl" class="lightbox" @click="lightboxUrl = ''">
      <button type="button" @click.stop="lightboxUrl = ''">×</button>
      <img :src="lightboxUrl" alt="" @click.stop />
    </div>

    <TagFilterPanel :tag="filterTag" @close="filterTag = null" @jump="handleTagJump" />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import {
  deleteMessage,
  favoriteMessage,
  fetchFavorites,
  fetchMessages,
  fetchMessagesNearDate,
  fetchSettings,
  unfavoriteMessage,
} from "@/lib/api";
import type { Message } from "@/lib/types";
import type { UserSettings } from "@/lib/settings-types";
import type { AiStreamState } from "@/lib/ai-content";
import { getQuotedMessageIds } from "@/lib/quote";
import { applyAvatarTransparency } from "@/lib/avatar-style";
import { scrollToMessage } from "@/lib/scroll-to-message";
import MessageRow from "@/components/MessageRow.vue";
import StreamAiRow from "@/components/StreamAiRow.vue";
import ChatEditor from "@/components/ChatEditor.vue";
import ScrollToBottomButton from "@/components/ScrollToBottomButton.vue";
import ChatSkeleton from "@/components/ChatSkeleton.vue";
import FavoritesBar from "@/components/FavoritesBar.vue";
import TagFilterPanel from "@/components/TagFilterPanel.vue";

const MESSAGE_HIGHLIGHT_MS = 2800;
const BOTTOM_THRESHOLD = 160;
const PAGE_LIMIT = 60;
const LOAD_MORE_THRESHOLD = 500;

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

// 分页 / 窗口状态
const hasMoreBefore = ref(false);
const hasMoreAfter = ref(false);
const loadingOlder = ref(false);
const loadingNewer = ref(false);
const favorites = ref<Message[]>([]);
const filterTag = ref<string | null>(null);

let highlightTimer: ReturnType<typeof setTimeout> | null = null;
let resizeFrame = 0;
let streamScrollFrame = 0;

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
  // 还有更晚的消息未加载时，视觉底部并非真正底部
  const trulyAtBottom = nearBottom && !hasMoreAfter.value;
  stickToBottom.value = trulyAtBottom;
  atBottom.value = trulyAtBottom;
}

function onWindowScroll() {
  syncAtBottom();
  void maybeLoadMore();
}

async function maybeLoadMore() {
  const el = document.documentElement;
  if (el.scrollTop < LOAD_MORE_THRESHOLD) await loadOlder();
  const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
  if (distanceToBottom < LOAD_MORE_THRESHOLD) await loadNewer();
}

async function loadOlder() {
  if (loadingOlder.value || !hasMoreBefore.value || !messages.value.length) return;
  loadingOlder.value = true;
  const oldest = messages.value[0];
  const doc = document.documentElement;
  const prevHeight = doc.scrollHeight;
  const prevTop = window.scrollY;
  try {
    const res = await fetchMessages({ before: oldest.id, limit: PAGE_LIMIT });
    if (res.items.length) {
      messages.value = [...res.items, ...messages.value];
      hasMoreBefore.value = res.hasMoreBefore;
      await nextTick();
      // 在顶部插入内容后修正滚动位置，保持视口稳定
      window.scrollTo({ top: prevTop + (doc.scrollHeight - prevHeight) });
    } else {
      hasMoreBefore.value = false;
    }
  } catch {
    /* 静默失败，下次滚动可重试 */
  } finally {
    loadingOlder.value = false;
  }
}

async function loadNewer() {
  if (loadingNewer.value || !hasMoreAfter.value || !messages.value.length) return;
  loadingNewer.value = true;
  const newest = messages.value[messages.value.length - 1];
  try {
    const res = await fetchMessages({ after: newest.id, limit: PAGE_LIMIT });
    if (res.items.length) {
      messages.value = [...messages.value, ...res.items];
      hasMoreAfter.value = res.hasMoreAfter;
    } else {
      hasMoreAfter.value = false;
    }
  } catch {
    /* 静默失败 */
  } finally {
    loadingNewer.value = false;
  }
}

async function reloadLatest() {
  const res = await fetchMessages({ limit: PAGE_LIMIT });
  messages.value = res.items;
  hasMoreBefore.value = res.hasMoreBefore;
  hasMoreAfter.value = false;
  stickToBottom.value = true;
  atBottom.value = true;
  await scrollToLatest("auto", true);
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
    const [list, cfg, favs] = await Promise.all([
      fetchMessages({ limit: PAGE_LIMIT }),
      fetchSettings(),
      fetchFavorites().catch(() => []),
    ]);
    messages.value = list.items;
    hasMoreBefore.value = list.hasMoreBefore;
    hasMoreAfter.value = list.hasMoreAfter;
    settings.value = cfg;
    favorites.value = favs;
    applyAvatarTransparency(cfg.avatarTransparent);
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

async function handleScrollToBottom() {
  if (hasMoreAfter.value) {
    await reloadLatest();
    return;
  }
  stickToBottom.value = true;
  atBottom.value = true;
  void scrollToLatest("smooth", true);
}

function setQuote(message: Message) {
  quote.value = message;
}

async function toggleFavorite(id: string) {
  const isFav = favorites.value.some((f) => f.id === id);
  try {
    if (isFav) {
      await unfavoriteMessage(id);
      favorites.value = favorites.value.filter((f) => f.id !== id);
    } else {
      const updated = await favoriteMessage(id);
      favorites.value = [updated, ...favorites.value];
    }
  } catch {
    error.value = isFav ? "取消收藏失败" : "收藏失败";
  }
}

async function handleDelete(id: string) {
  try {
    await deleteMessage(id);
    messages.value = messages.value.filter((m) => m.id !== id);
    if (quote.value?.id === id) quote.value = null;
    favorites.value = favorites.value.filter((f) => f.id !== id);
  } catch {
    error.value = "删除失败";
  }
}

async function handleTagJump(id: string) {
  filterTag.value = null;
  await jumpToMessage(id);
}

async function handleJumpDate(date: string) {
  try {
    const res = await fetchMessagesNearDate(date);
    messages.value = res.items;
    hasMoreBefore.value = res.hasMoreBefore;
    hasMoreAfter.value = res.hasMoreAfter;
    stickToBottom.value = false;
    atBottom.value = false;
    await nextTick();
    if (res.anchorId) highlightMessage(res.anchorId);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "跳转失败";
  }
}

function handleEdited(updated: Message) {
  const index = messages.value.findIndex((m) => m.id === updated.id);
  if (index !== -1) messages.value[index] = updated;
  const favIndex = favorites.value.findIndex((f) => f.id === updated.id);
  if (favIndex !== -1) favorites.value[favIndex] = updated;
}

function highlightMessage(id: string) {
  scrollToMessage(id);
  if (highlightTimer) clearTimeout(highlightTimer);
  highlightedMessageId.value = id;
  highlightTimer = setTimeout(() => {
    highlightedMessageId.value = null;
    highlightTimer = null;
  }, MESSAGE_HIGHLIGHT_MS);
}

async function jumpToMessage(id: string) {
  if (messages.value.some((m) => m.id === id)) {
    highlightMessage(id);
    return;
  }
  // 目标不在当前窗口：围绕它加载一段上下文再定位
  try {
    const res = await fetchMessages({ around: id, limit: PAGE_LIMIT });
    if (!res.items.some((m) => m.id === id)) {
      error.value = "原文可能已被删除";
      return;
    }
    messages.value = res.items;
    hasMoreBefore.value = res.hasMoreBefore;
    hasMoreAfter.value = res.hasMoreAfter;
    stickToBottom.value = false;
    atBottom.value = false;
    await nextTick();
    highlightMessage(id);
  } catch {
    error.value = "定位失败";
  }
}

async function handleSent(message: Message) {
  error.value = "";
  if (hasMoreAfter.value) {
    // 正在浏览历史时发送：回到最新一页，新消息自然出现在底部
    await reloadLatest();
    return;
  }
  scrollAfterSend.value = true;
  stickToBottom.value = true;
  atBottom.value = true;
  messages.value.push(message);
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
