<template>
  <div ref="zoneRef" class="chat-editor-zone">
    <div class="chat-editor-inner" :style="{ maxWidth: `${layoutWidth}px` }">
      <div :class="['chat-editor-panel', { 'chat-editor-panel--expanded': expanded }]">
        <QuoteCard v-if="quotingMessage" :quote="quotingMessage" compact show-close @close="$emit('clearQuote')" />

        <textarea ref="textareaRef" v-model="input" :rows="expanded ? undefined : 5" :disabled="sending || aiThinking"
          :class="['chat-editor-input', { 'chat-editor-input--expanded': expanded }]" :placeholder="placeholder"
          @keydown="handleKeyDown" />

        <ImagePreviewBar :items="pendingImages" :uploading="uploading" @remove="removePending" />

        <div class="chat-editor-footer">
          <div class="chat-editor-tools">
            <button type="button" :class="['toolbar-btn', { 'toolbar-btn--active': aiEnabled }]"
              :disabled="sending || aiThinking" :title="aiEnabled ? '关闭 AI（发送时自动回复）' : '开启 AI（发送时自动回复）'"
              @click="toggleAi">
              <AiIcon />
            </button>
            <EmojiPicker :disabled="sending || aiThinking" @pick="insertEmoji" />
            <button type="button" class="toolbar-btn" :disabled="sending || aiThinking" title="图片"
              @click="imageInputRef?.click()">
              <ImageIcon />
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
import { sendImageMessage, sendTextMessage } from "@/lib/api";
import { shouldCallAi, shouldInvokeAi } from "@/lib/ai-trigger";
import { readAiEnabled, writeAiEnabled } from "@/lib/ai-toggle";
import type { AiStreamState } from "@/lib/ai-content";
import { streamAiReply } from "@/lib/ai-stream";
import type { Message } from "@/lib/types";
import {
  createPendingImage,
  isImageFile,
  revokeAllPendingImages,
  revokePendingImage,
  type PendingImage,
} from "@/lib/pending-image";
import ImagePreviewBar from "./ImagePreviewBar.vue";
import QuoteCard from "./QuoteCard.vue";
import EmojiPicker from "./EmojiPicker.vue";
import { GearIcon } from "./icons";
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
const uploadProgress = ref<number | null>(null);
const pendingImages = ref<PendingImage[]>([]);
const expanded = ref(false);
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const imageInputRef = ref<HTMLInputElement | null>(null);
const zoneRef = ref<HTMLDivElement | null>(null);

const quoteId = computed(() => props.quotingMessage?.id ?? null);
const uploading = computed(() => sending.value && pendingImages.value.length > 0);
const canSend = computed(
  () => !sending.value && !aiThinking.value && (input.value.trim().length > 0 || pendingImages.value.length > 0),
);

const placeholder = computed(() => {
  if (props.quotingMessage) return "回复引用消息……支持 Markdown";
  if (pendingImages.value.length > 0) {
    return aiEnabled.value
      ? "添加说明（Markdown），Enter 发送，AI 已开启"
      : "添加说明（Markdown），Enter 发送；@ai 可召唤 AI";
  }
  return aiEnabled.value
    ? "输入消息，支持 Markdown，AI 已开启，Enter 发送"
    : "输入消息，支持 Markdown；输入 @ai 或点工具栏 AI 按钮";
});

const sendLabel = computed(() => {
  if (uploading.value && uploadProgress.value !== null) return `上传 ${uploadProgress.value}%`;
  if (aiThinking.value) return "AI 思考中…";
  if (sending.value) return "发送中…";
  return "发送";
});

onMounted(() => {
  aiEnabled.value = readAiEnabled();
  textareaRef.value?.focus();

  const el = zoneRef.value;
  if (!el) return;
  const report = () => emit("zoneHeightChange", el.offsetHeight);
  report();
  const observer = new ResizeObserver(report);
  observer.observe(el);
  onUnmounted(() => observer.disconnect());
});

watch(
  () => [props.quotingMessage, expanded.value, pendingImages.value.length] as const,
  () => {
    const el = zoneRef.value;
    if (el) emit("zoneHeightChange", el.offsetHeight);
  },
);

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

function insertEmoji(emoji: string) {
  const el = textareaRef.value;
  if (!el) {
    input.value += emoji;
    return;
  }
  const start = el.selectionStart;
  const end = el.selectionEnd;
  input.value = input.value.slice(0, start) + emoji + input.value.slice(end);
  requestAnimationFrame(() => {
    el.focus();
    const pos = start + emoji.length;
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
  pendingImages.value.push(...list.map((file) => createPendingImage(file)));
}

function onImageChange(event: Event) {
  const target = event.target as HTMLInputElement;
  addPendingImages(target.files);
  target.value = "";
}

function removePending(id: string) {
  if (sending.value) return;
  const target = pendingImages.value.find((item) => item.id === id);
  if (target) revokePendingImage(target);
  pendingImages.value = pendingImages.value.filter((item) => item.id !== id);
}

async function invokeAiIfNeeded(text: string, messageId: string) {
  if (!shouldCallAi(text, aiEnabled.value)) return;
  const force = aiEnabled.value && !shouldInvokeAi(text);
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
  const text = input.value.trim();
  const images = [...pendingImages.value];
  if ((!text && images.length === 0) || !canSend.value) return;

  sending.value = true;
  uploadProgress.value = null;

  try {
    if (images.length === 0) {
      const msg = await sendTextMessage({ content: text, quoteId: quoteId.value });
      emit("clearQuote");
      emit("sent", msg);
      input.value = "";
      await invokeAiIfNeeded(text, msg.id);
      return;
    }

    const msg = await sendImageMessage(images.map((item) => item.file), text, quoteId.value, (loaded, total) => {
      if (total > 0) uploadProgress.value = Math.round((loaded / total) * 100);
    });

    if (quoteId.value) emit("clearQuote");
    emit("sent", msg);
    input.value = "";
    revokeAllPendingImages(images);
    pendingImages.value = [];
    await invokeAiIfNeeded(text, msg.id);
  } catch (err) {
    emit("error", err instanceof Error ? err.message : "发送失败");
  } finally {
    sending.value = false;
    uploadProgress.value = null;
    textareaRef.value?.focus();
  }
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submit();
  }
}
</script>
