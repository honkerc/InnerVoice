<template>
  <AiMessageBlock v-if="isAi" :message-id="message.id" :time-label="aiTimeLabel" :copy-text-value="copyTextValue"
    :can-quote="canQuote" can-pin :is-pinned="pinned" :highlighted="highlighted" :quote="message.quote"
    @quote="$emit('quote', message)" @pin="$emit('pin', message.id)" @jump-quote="$emit('jumpQuote', $event)">
    <template v-if="message.type === 'image' && message.mediaUrl">
      <MessageCaption :content="message.content" />
      <img class="msg-image" :src="message.mediaUrl" alt="" @click="$emit('previewImage', message.mediaUrl!)" />
    </template>
    <template v-else-if="message.type === 'media_group' && message.attachments?.length">
      <MessageCaption :content="message.content" />
      <div class="msg-images">
        <img v-for="item in message.attachments.filter((a) => a.type === 'image')" :key="item.url" class="msg-image"
          :src="item.url" :alt="item.name" @click="$emit('previewImage', item.url)" />
      </div>
    </template>
    <AiMessageContent v-else :content="message.content" @preview-image="$emit('previewImage', $event)" />
  </AiMessageBlock>

  <section v-else class="msg-row" :class="[rowClass, { 'is-highlighted': highlighted }]" :id="`message-${message.id}`">
    <div class="msg-meta">{{ metaLabel }}</div>
    <div class="msg-body" :class="{ 'msg-body--right': alignRight }">
      <div class="msg-avatar" :class="{ 'msg-avatar--transparent': avatarTransparent }">
        <img v-if="avatarUrl" :src="avatarUrl" alt="" />
        <span v-else>{{ avatarLabel }}</span>
      </div>
      <div class="msg-bubble" :class="[
        alignRight ? 'msg-bubble--me' : 'msg-bubble--past',
        { 'is-pinned': pinned },
      ]">
        <QuotePreview v-if="message.quote" :quote="message.quote" @jump="$emit('jumpQuote', message.quote!.id)" />
        <template v-if="message.type === 'image' && message.mediaUrl">
          <MessageCaption :content="message.content" />
          <img class="msg-image" :src="message.mediaUrl" alt="" @click="$emit('previewImage', message.mediaUrl!)" />
        </template>
        <template v-else-if="message.type === 'media_group' && message.attachments?.length">
          <MessageCaption :content="message.content" />
          <div class="msg-images">
            <img v-for="item in message.attachments.filter((a) => a.type === 'image')" :key="item.url" class="msg-image"
              :src="item.url" :alt="item.name" @click="$emit('previewImage', item.url)" />
          </div>
        </template>
        <MarkdownView v-else :content="message.content" @preview-image="$emit('previewImage', $event)" />
      </div>
    </div>
    <div class="msg-row__actions" :class="alignRight ? 'msg-row__actions--end' : 'msg-row__actions--start'">
      <div class="message-actions-wrap" :class="{ 'message-actions-wrap--pinned': pinned }">
        <MessageActions :copy-text-value="copyTextValue" :can-quote="canQuote" can-pin :is-pinned="pinned"
          @quote="$emit('quote', message)" @pin="$emit('pin', message.id)" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Message } from "@/lib/types";
import { formatMessageTime, isToday } from "@/lib/date";
import { aiMetaLabel } from "@/lib/ai-label";
import { getMessageCopyText } from "@/lib/message-copy";
import { isAiRole } from "@/lib/quote";
import QuotePreview from "./QuotePreview.vue";
import AiMessageBlock from "./AiMessageBlock.vue";
import AiMessageContent from "./AiMessageContent.vue";
import MessageCaption from "./MessageCaption.vue";
import MarkdownView from "./MarkdownView.vue";
import MessageActions from "./MessageActions.vue";

const props = defineProps<{
  message: Message;
  pinned?: boolean;
  highlighted?: boolean;
  canQuote?: boolean;
  userAvatar?: string | null;
  userName?: string;
  aiModelLabel?: string;
  avatarTransparent?: boolean;
}>();

defineEmits<{
  quote: [message: Message];
  pin: [id: string];
  jumpQuote: [id: string];
  previewImage: [url: string];
}>();

const isAi = computed(() => isAiRole(props.message.role));
const alignRight = computed(() => props.message.role === "me" && isToday(props.message.createdAt));
const rowClass = computed(() => (alignRight.value ? "msg-row--right" : "msg-row--left"));
const displayName = computed(() => props.message.authorDisplayName || props.userName || "我");
const metaLabel = computed(() => {
  if (alignRight.value) {
    return `今天 · ${formatMessageTime(props.message.createdAt)}`;
  }
  return `${displayName.value} · ${formatMessageTime(props.message.createdAt)}`;
});
const aiTimeLabel = computed(() =>
  aiMetaLabel(props.aiModelLabel, formatMessageTime(props.message.createdAt)),
);
const avatarUrl = computed(() => props.message.authorAvatarUrl || props.userAvatar);
const avatarLabel = computed(() => (props.message.authorDisplayName || props.userName || "我").slice(0, 1));
const copyTextValue = computed(() => getMessageCopyText(props.message));
</script>
