<template>
  <AiMessageBlock v-if="isAi" :message-id="message.id" :time-label="aiTimeLabel" :copy-text-value="copyTextValue"
    :can-quote="canQuote" can-pin :is-pinned="pinned" :highlighted="highlighted" :quote="message.quote"
    @quote="$emit('quote', message)" @pin="$emit('pin', message.id)" @delete="$emit('delete', message.id)"
    @jump-quote="$emit('jumpQuote', $event)">
    <template v-if="(message.type === 'image' || message.type === 'video' || message.type === 'file') && message.mediaUrl">
      <MessageCaption :content="displayContent" />
      <MessageAttachment :url="message.mediaUrl" :name="message.mediaName" :type="message.type"
        @preview-image="$emit('previewImage', $event)" />
    </template>
    <template v-else-if="message.type === 'media_group' && message.attachments?.length">
      <MessageCaption :content="displayContent" />
      <div class="msg-images">
        <MessageAttachment v-for="item in message.attachments" :key="item.url" :url="item.url" :name="item.name"
          :type="item.type" @preview-image="$emit('previewImage', $event)" />
      </div>
    </template>
    <AiMessageContent v-else :content="displayContent" @preview-image="$emit('previewImage', $event)" />
    <TagChips :tags="message.tags" @select="$emit('filterTag', $event)" />
  </AiMessageBlock>

  <section v-else class="msg-row" :class="[rowClass, { 'is-highlighted': highlighted }]" :id="`message-${message.id}`">
    <div class="msg-meta">{{ metaLabel }}</div>
    <div class="msg-body" :class="{ 'msg-body--right': alignRight, 'msg-body--editing': editing }">
      <div class="msg-avatar">
        <img v-if="avatarUrl" :src="avatarUrl" alt="" />
        <span v-else>{{ avatarLabel }}</span>
      </div>
      <div class="msg-bubble" :class="[
        alignRight ? 'msg-bubble--me' : 'msg-bubble--past',
        { 'is-pinned': pinned, 'msg-bubble--editing': editing },
      ]">
        <QuotePreview v-if="message.quote" :quote="message.quote" @jump="$emit('jumpQuote', message.quote!.id)" />
        <div v-if="editing" class="msg-edit">
          <textarea ref="editTextareaRef" v-model="editDraft" class="field-input field-textarea msg-edit__textarea"
            :disabled="savingEdit" :placeholder="message.type === 'text' ? '消息内容' : '说明文字（可留空）'"
            @keydown.esc="cancelEdit" @blur="handleTextareaBlur" @input="autoGrow" />
          <p v-if="editError" class="settings-message settings-message--error">{{ editError }}</p>
          <div class="msg-edit__actions">
            <button type="button" class="settings-btn settings-btn--ghost" :disabled="savingEdit"
              @mousedown.prevent @click="cancelEdit">
              取消
            </button>
            <button type="button" class="settings-btn settings-btn--primary" :disabled="savingEdit"
              @mousedown.prevent @click="saveEdit">
              {{ savingEdit ? "保存中…" : "保存" }}
            </button>
          </div>
        </div>
        <template v-else-if="(message.type === 'image' || message.type === 'video' || message.type === 'file') && message.mediaUrl">
          <MessageCaption :content="displayContent" />
          <MessageAttachment :url="message.mediaUrl" :name="message.mediaName" :type="message.type"
            @preview-image="$emit('previewImage', $event)" />
        </template>
        <template v-else-if="message.type === 'media_group' && message.attachments?.length">
          <MessageCaption :content="displayContent" />
          <div class="msg-images">
            <MessageAttachment v-for="item in message.attachments" :key="item.url" :url="item.url" :name="item.name"
              :type="item.type" @preview-image="$emit('previewImage', $event)" />
          </div>
        </template>
        <MarkdownView v-else :content="displayContent" @preview-image="$emit('previewImage', $event)" />
        <TagChips :tags="message.tags" @select="$emit('filterTag', $event)" />
      </div>
    </div>
    <div v-if="!editing" class="msg-row__actions" :class="alignRight ? 'msg-row__actions--end' : 'msg-row__actions--start'">
      <div class="message-actions-wrap" :class="{ 'message-actions-wrap--pinned': pinned }">
        <MessageActions :copy-text-value="copyTextValue" :can-quote="canQuote" :can-edit="canEdit" can-pin
          :is-pinned="pinned" can-delete @quote="$emit('quote', message)" @edit="startEdit"
          @pin="$emit('pin', message.id)" @delete="$emit('delete', message.id)" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import type { Message } from "@/lib/types";
import { formatMessageTime, isToday } from "@/lib/date";
import { aiMetaLabel } from "@/lib/ai-label";
import { getMessageCopyText } from "@/lib/message-copy";
import { isAiRole } from "@/lib/quote";
import { stripKnownTags } from "@/lib/tags";
import { editMessage } from "@/lib/api";
import QuotePreview from "./QuotePreview.vue";
import AiMessageBlock from "./AiMessageBlock.vue";
import AiMessageContent from "./AiMessageContent.vue";
import MessageCaption from "./MessageCaption.vue";
import MarkdownView from "./MarkdownView.vue";
import MessageActions from "./MessageActions.vue";
import MessageAttachment from "./MessageAttachment.vue";
import TagChips from "./TagChips.vue";

const props = defineProps<{
  message: Message;
  pinned?: boolean;
  highlighted?: boolean;
  canQuote?: boolean;
  userAvatar?: string | null;
  userName?: string;
  aiModelLabel?: string;
}>();

const emit = defineEmits<{
  quote: [message: Message];
  pin: [id: string];
  delete: [id: string];
  jumpQuote: [id: string];
  previewImage: [url: string];
  edited: [message: Message];
  filterTag: [tag: string];
}>();

const isAi = computed(() => isAiRole(props.message.role));
const canEdit = computed(() => props.message.role === "me");
const displayContent = computed(() => stripKnownTags(props.message.content, props.message.tags));

const editing = ref(false);
const editDraft = ref("");
const savingEdit = ref(false);
const editError = ref("");
const editTextareaRef = ref<HTMLTextAreaElement | null>(null);

function autoGrow() {
  const el = editTextareaRef.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
}

function startEdit() {
  editDraft.value = props.message.content;
  editError.value = "";
  editing.value = true;
  nextTick(autoGrow);
}

function cancelEdit() {
  editing.value = false;
}

function handleTextareaBlur() {
  if (savingEdit.value) return;
  cancelEdit();
}

async function saveEdit() {
  if (savingEdit.value) return;
  const content = editDraft.value.trim();
  if (props.message.type === "text" && !content) {
    editError.value = "内容不能为空";
    return;
  }
  savingEdit.value = true;
  editError.value = "";
  try {
    const updated = await editMessage(props.message.id, content);
    emit("edited", updated);
    editing.value = false;
  } catch (err) {
    editError.value = err instanceof Error ? err.message : "修改失败";
  } finally {
    savingEdit.value = false;
  }
}
const alignRight = computed(() => props.message.role === "me" && isToday(props.message.createdAt));
const rowClass = computed(() => (alignRight.value ? "msg-row--right" : "msg-row--left"));
const metaLabel = computed(() =>
  `${alignRight.value ? "今天" : "过往"} · ${formatMessageTime(props.message.createdAt)}`,
);
const aiTimeLabel = computed(() =>
  aiMetaLabel(props.aiModelLabel, formatMessageTime(props.message.createdAt)),
);
const avatarUrl = computed(() => props.message.authorAvatarUrl || props.userAvatar);
const avatarLabel = computed(() => (props.message.authorDisplayName || props.userName || "我").slice(0, 1));
const copyTextValue = computed(() => getMessageCopyText(props.message));
</script>
