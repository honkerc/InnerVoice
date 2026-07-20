<template>
  <div ref="zoneRef" class="chat-editor-zone">
    <div class="chat-editor-inner" :style="{ maxWidth: `${layoutWidth}px` }">
      <div :class="['chat-editor-panel', { 'chat-editor-panel--expanded': expanded }]">
        <div v-if="menuOpen" class="slash-menu">
          <template v-if="slash.kind === 'search'">
            <ul v-if="results.length" class="slash-menu__list">
              <li v-for="(item, i) in results" :key="item.id">
                <button type="button" class="slash-menu__item" :class="{ 'is-active': i === activeIndex }"
                  @mousedown.prevent @mouseenter="activeIndex = i" @click="selectResult(item)">
                  <span class="slash-menu__text"><span>{{ item.snippet.pre }}</span><mark
                      v-if="item.snippet.match">{{ item.snippet.match }}</mark><span>{{ item.snippet.post }}</span></span>
                  <span class="slash-menu__date">{{ item.date }}</span>
                </button>
              </li>
            </ul>
            <p v-else class="slash-menu__empty">{{ searching ? "搜索中…" : "无匹配结果" }}</p>
          </template>
          <div v-else class="slash-menu__hint">
            <button type="button" class="slash-menu__item" @mousedown.prevent @click="applyAiPrefix">
              <span class="slash-menu__cmd">/ai</span>
              <span class="slash-menu__text">{{ slash.kind === 'ai' ? '回车发送，让 AI 回应你' : '呼出 AI 对话' }}</span>
            </button>
            <p class="slash-menu__tip">输入 /关键词 搜索历史记录</p>
          </div>
        </div>

        <QuoteCard v-if="quotingMessage" :quote="quotingMessage" compact show-close @close="$emit('clearQuote')" />

        <textarea ref="textareaRef" v-model="input" :rows="expanded ? undefined : 3" :disabled="sending || aiThinking"
          :class="['chat-editor-input', { 'chat-editor-input--expanded': expanded }]" :placeholder="placeholder"
          @keydown="handleKeyDown" />

        <ImagePreviewBar :items="pendingMedia" :uploading="uploading" @remove="removePending" />

        <div class="chat-editor-footer">
          <div class="chat-editor-tools">
            <EmojiPicker :disabled="sending || aiThinking" @pick="insertText" />
            <button type="button" :class="['toolbar-btn', { 'toolbar-btn--active': aiEnabled }]"
              :disabled="sending || aiThinking" :title="aiEnabled ? '关闭 AI（发送时自动回复）' : '开启 AI（发送时自动回复）'"
              @click="toggleAi">
              <AiIcon />
            </button>
            <TemplatePicker :disabled="sending || aiThinking" @pick="insertText" />
            <button type="button" class="toolbar-btn" :disabled="sending || aiThinking" title="图片"
              @click="imageInputRef?.click()">
              <ImageIcon />
            </button>
            <button type="button" class="toolbar-btn" :disabled="sending || aiThinking" title="附件（视频/文件）"
              @click="attachInputRef?.click()">
              <IconAttach />
            </button>
            <AiReviewPicker v-if="false" :disabled="sending || aiThinking || aiReviewLoading"
              @pick="handleAiReview" />
            <button v-if="false" type="button" class="toolbar-btn" :disabled="sending || aiThinking" title="按日期跳转"
              @click="openDatePicker">
              <IconCalendar />
            </button>
            <button type="button" class="toolbar-btn" :disabled="sending || aiThinking"
              :title="expanded ? '退出放大' : '放大输入框'" @click="toggleExpanded">
              <CollapseIcon v-if="expanded" />
              <ExpandIcon v-else />
            </button>
            <RouterLink to="/settings" title="设置" class="toolbar-link">
              <GearIcon />
            </RouterLink>
            <input ref="imageInputRef" type="file" accept="image/*" multiple class="hidden" @change="onImageChange" />
            <input
              ref="attachInputRef"
              type="file"
              accept="video/*,.pdf,.doc,.docx,.txt,.zip,.rar,.csv,.xlsx,.pptx"
              multiple
              class="hidden"
              @change="onAttachChange"
            />
            <input v-if="false" ref="dateInputRef" type="date" class="hidden" @change="onDateChange" />
            <!-- <span class="chat-editor-hint">Shift+Enter 换行</span> -->
          </div>
          <button type="button" class="chat-editor-send" :disabled="!canSend" @click="submit">
            {{ sendLabel }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { fetchMessages, requestAiReview, sendMediaMessage, sendTextMessage } from "@/lib/api";
import { shouldCallAi, shouldInvokeAi } from "@/lib/ai-trigger";
import { readAiEnabled, writeAiEnabled } from "@/lib/ai-toggle";
import type { AiStreamState } from "@/lib/ai-content";
import { streamAiReply } from "@/lib/ai-stream";
import { getMessageCopyText } from "@/lib/message-copy";
import { buildSnippet, formatShortDate, parseSlash, unescapeSlash, type SnippetParts } from "@/lib/slash-command";
import { readDraft, writeDraft } from "@/lib/draft-storage";
import type { AiReviewPeriod, Message } from "@/lib/types";
import {
  createPendingMedia,
  isImageFile,
  revokeAllPendingMedia,
  revokePendingMedia,
  type PendingMedia,
} from "@/lib/pending-media";
import ImagePreviewBar from "./ImagePreviewBar.vue";
import QuoteCard from "./QuoteCard.vue";
import EmojiPicker from "./EmojiPicker.vue";
import TemplatePicker from "./TemplatePicker.vue";
import AiReviewPicker from "./AiReviewPicker.vue";
import { GearIcon, IconAttach, IconCalendar } from "./icons";
import AiIcon from "./toolbar/AiIcon.vue";
import ImageIcon from "./toolbar/ImageIcon.vue";
import ExpandIcon from "./toolbar/ExpandIcon.vue";
import CollapseIcon from "./toolbar/CollapseIcon.vue";

const props = defineProps<{
  layoutWidth: number;
  quotingMessage: Message | null;
}>();

const emit = defineEmits<{
  clearQuote: [];
  sent: [message: Message];
  error: [message: string];
  jump: [id: string];
  jumpDate: [date: string];
  aiStreamStart: [];
  aiStreamUpdate: [state: AiStreamState];
  aiStreamDone: [message: Message];
  aiStreamClear: [];
  zoneHeightChange: [height: number];
}>();

const input = ref("");
const sending = ref(false);
const aiThinking = ref(false);
const aiEnabled = ref(false);
const aiReviewLoading = ref(false);
const uploadProgress = ref<number | null>(null);
const pendingMedia = ref<PendingMedia[]>([]);
const expanded = ref(false);
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const imageInputRef = ref<HTMLInputElement | null>(null);
const attachInputRef = ref<HTMLInputElement | null>(null);
const dateInputRef = ref<HTMLInputElement | null>(null);
const zoneRef = ref<HTMLDivElement | null>(null);

const quoteId = computed(() => props.quotingMessage?.id ?? null);
const uploading = computed(() => sending.value && pendingMedia.value.length > 0);

// “/” 斜杠命令
interface SearchResult {
  id: string;
  snippet: SnippetParts;
  date: string;
}
const results = ref<SearchResult[]>([]);
const searching = ref(false);
const activeIndex = ref(0);
let searchTimer: ReturnType<typeof setTimeout> | null = null;
let searchSeq = 0;

const slash = computed(() => parseSlash(input.value));
const inSearch = computed(() => slash.value.kind === "search");
const menuOpen = computed(() => {
  const s = slash.value;
  if (s.kind === "search") return s.query.length > 0;
  return s.kind === "menu" || s.kind === "ai";
});

const canSend = computed(
  () =>
    !sending.value &&
    !aiThinking.value &&
    !inSearch.value &&
    (input.value.trim().length > 0 || pendingMedia.value.length > 0),
);

watch(
  () => (slash.value.kind === "search" ? slash.value.query : ""),
  (query) => {
    activeIndex.value = 0;
    if (searchTimer) clearTimeout(searchTimer);
    if (!query) {
      searchSeq++;
      results.value = [];
      searching.value = false;
      return;
    }
    searching.value = true;
    searchTimer = setTimeout(() => void runSearch(query), 200);
  },
);

async function runSearch(query: string) {
  const current = ++searchSeq;
  try {
    const res = await fetchMessages({ q: query, limit: 12 });
    if (current !== searchSeq) return;
    results.value = res.items.map((message) => ({
      id: message.id,
      snippet: buildSnippet(getMessageCopyText(message) || message.content, query),
      date: formatShortDate(message.createdAt),
    }));
  } catch {
    if (current === searchSeq) results.value = [];
  } finally {
    if (current === searchSeq) searching.value = false;
  }
}

function selectResult(item: SearchResult) {
  emit("jump", item.id);
  input.value = "";
  results.value = [];
}

function applyAiPrefix() {
  input.value = "/ai ";
  requestAnimationFrame(() => {
    const el = textareaRef.value;
    el?.focus();
    el?.setSelectionRange(input.value.length, input.value.length);
  });
}

const placeholder = computed(() => {
  if (props.quotingMessage) return "回复引用消息……支持 Markdown";
  if (pendingMedia.value.length > 0) {
    return aiEnabled.value
      ? "添加说明（Markdown），Enter 发送，AI 已开启"
      : "添加说明（Markdown），Enter 发送；@ai 可召唤 AI";
  }
  return aiEnabled.value
    ? "输入消息，支持 Markdown，AI 已开启，Enter 发送"
    : "输入消息，支持 Markdown；/ 搜索历史，/ai 呼出 AI";
});

const sendLabel = computed(() => {
  if (uploading.value && uploadProgress.value !== null) return `上传 ${uploadProgress.value}%`;
  if (aiThinking.value) return "AI 思考中…";
  if (sending.value) return "发送中…";
  return "发送";
});

onMounted(() => {
  aiEnabled.value = readAiEnabled();
  input.value = readDraft();
  requestAnimationFrame(() => {
    const el = textareaRef.value;
    el?.focus();
    el?.setSelectionRange(input.value.length, input.value.length);
  });

  const el = zoneRef.value;
  if (!el) return;
  const report = () => emit("zoneHeightChange", el.offsetHeight);
  report();
  const observer = new ResizeObserver(report);
  observer.observe(el);
  onUnmounted(() => observer.disconnect());
});

watch(
  () => [props.quotingMessage, expanded.value, pendingMedia.value.length] as const,
  () => {
    const el = zoneRef.value;
    if (el) emit("zoneHeightChange", el.offsetHeight);
  },
);

let draftTimer: ReturnType<typeof setTimeout> | null = null;
watch(input, (value) => {
  if (draftTimer) clearTimeout(draftTimer);
  draftTimer = setTimeout(() => writeDraft(value), 300);
});

function clearDraftNow() {
  if (draftTimer) clearTimeout(draftTimer);
  writeDraft("");
}

let escapeHandler: ((event: KeyboardEvent) => void) | null = null;

watch(expanded, (value) => {
  if (escapeHandler) {
    window.removeEventListener("keydown", escapeHandler);
    escapeHandler = null;
  }
  if (!value) return;
  escapeHandler = (event: KeyboardEvent) => {
    if (event.key === "Escape") {
      expanded.value = false;
      requestAnimationFrame(() => textareaRef.value?.focus());
    }
  };
  window.addEventListener("keydown", escapeHandler);
});

onUnmounted(() => {
  if (escapeHandler) window.removeEventListener("keydown", escapeHandler);
  if (searchTimer) clearTimeout(searchTimer);
  if (draftTimer) clearTimeout(draftTimer);
});

function toggleAi() {
  aiEnabled.value = !aiEnabled.value;
  writeAiEnabled(aiEnabled.value);
  requestAnimationFrame(() => textareaRef.value?.focus());
}

function toggleExpanded() {
  expanded.value = !expanded.value;
  requestAnimationFrame(() => textareaRef.value?.focus());
}

function insertText(text: string) {
  const el = textareaRef.value;
  if (!el) {
    input.value += text;
    return;
  }
  const start = el.selectionStart;
  const end = el.selectionEnd;
  input.value = input.value.slice(0, start) + text + input.value.slice(end);
  requestAnimationFrame(() => {
    el.focus();
    const pos = start + text.length;
    el.setSelectionRange(pos, pos);
  });
}

function addPendingImages(files: FileList | File[] | null) {
  if (!files || sending.value) return;
  const list = Array.from(files).filter(isImageFile);
  if (!list.length) {
    emit("error", "请选择图片文件");
    return;
  }
  pendingMedia.value.push(...list.map((file) => createPendingMedia(file)));
}

function addPendingAttachments(files: FileList | File[] | null) {
  if (!files || sending.value) return;
  const list = Array.from(files);
  if (!list.length) return;
  pendingMedia.value.push(...list.map((file) => createPendingMedia(file)));
}

function onImageChange(event: Event) {
  const target = event.target as HTMLInputElement;
  addPendingImages(target.files);
  target.value = "";
}

function onAttachChange(event: Event) {
  const target = event.target as HTMLInputElement;
  addPendingAttachments(target.files);
  target.value = "";
}

function removePending(id: string) {
  if (sending.value) return;
  const target = pendingMedia.value.find((item) => item.id === id);
  if (target) revokePendingMedia(target);
  pendingMedia.value = pendingMedia.value.filter((item) => item.id !== id);
}

async function handleAiReview(period: AiReviewPeriod) {
  if (aiReviewLoading.value || sending.value || aiThinking.value) return;
  aiReviewLoading.value = true;
  try {
    const msg = await requestAiReview(period);
    emit("sent", msg);
  } catch (err) {
    emit("error", err instanceof Error ? err.message : "生成回顾失败");
  } finally {
    aiReviewLoading.value = false;
  }
}

function openDatePicker() {
  const el = dateInputRef.value;
  if (!el) return;
  if (typeof el.showPicker === "function") {
    el.showPicker();
  } else {
    el.click();
  }
}

function onDateChange(event: Event) {
  const value = (event.target as HTMLInputElement).value;
  if (value) emit("jumpDate", value);
}

async function invokeAiIfNeeded(text: string, messageId: string, forceAi = false) {
  const enabled = aiEnabled.value || forceAi;
  if (!shouldCallAi(text, enabled)) return;
  const force = enabled && !shouldInvokeAi(text);
  aiThinking.value = true;
  let finished = false;
  try {
    await streamAiReply(messageId, force, {
      onStart: () => emit("aiStreamStart"),
      onUpdate: (state) => emit("aiStreamUpdate", state),
      onDone: (message) => {
        finished = true;
        emit("aiStreamDone", message);
      },
      onError: (message) => {
        finished = true;
        emit("aiStreamClear");
        emit("error", message);
      },
    });
  } finally {
    if (!finished) emit("aiStreamClear");
    aiThinking.value = false;
  }
}

async function submit() {
  const command = parseSlash(input.value);

  // 搜索模式：回车 = 定位当前高亮结果，而不是发送
  if (command.kind === "search") {
    const target = results.value[activeIndex.value];
    if (target) selectResult(target);
    return;
  }
  // 仅输入了 “/”：不发送
  if (command.kind === "menu") return;

  let text = unescapeSlash(input.value).trim();
  let forceAi = false;
  if (command.kind === "ai") {
    if (!command.question) {
      // “/ai” 无内容：顺手打开 AI 开关，清空输入
      if (!aiEnabled.value) toggleAi();
      input.value = "";
      return;
    }
    text = command.question;
    forceAi = true;
  }

  const media = [...pendingMedia.value];
  if ((!text && media.length === 0) || sending.value || aiThinking.value) return;

  sending.value = true;
  uploadProgress.value = null;

  try {
    if (media.length === 0) {
      const msg = await sendTextMessage({ content: text, quoteId: quoteId.value });
      emit("clearQuote");
      emit("sent", msg);
      input.value = "";
      clearDraftNow();
      await invokeAiIfNeeded(text, msg.id, forceAi);
      return;
    }

    const msg = await sendMediaMessage(media.map((item) => item.file), text, quoteId.value, (loaded, total) => {
      if (total > 0) uploadProgress.value = Math.round((loaded / total) * 100);
    });

    if (quoteId.value) emit("clearQuote");
    emit("sent", msg);
    input.value = "";
    clearDraftNow();
    revokeAllPendingMedia(media);
    pendingMedia.value = [];
    await invokeAiIfNeeded(text, msg.id, forceAi);
  } catch (err) {
    emit("error", err instanceof Error ? err.message : "发送失败");
  } finally {
    sending.value = false;
    uploadProgress.value = null;
    textareaRef.value?.focus();
  }
}

function handleKeyDown(event: KeyboardEvent) {
  // 搜索菜单打开时接管上下 / 回车 / Esc
  if (menuOpen.value && slash.value.kind === "search" && results.value.length) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      activeIndex.value = (activeIndex.value + 1) % results.value.length;
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      activeIndex.value = (activeIndex.value - 1 + results.value.length) % results.value.length;
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      input.value = "";
      return;
    }
  }
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submit();
  }
}
</script>
