export type MessageRole = "me" | "ai";
export type MessageType = "text" | "image" | "video" | "file" | "media_group";
export type AttachmentType = "image" | "video" | "file";

export interface MessageAttachment {
  type: AttachmentType;
  url: string;
  name: string;
}

export interface QuotePreview {
  id: string;
  role: MessageRole;
  type: MessageType;
  content: string;
  mediaUrl?: string;
  mediaName?: string;
}

export interface Message {
  id: string;
  createdAt: string;
  role: MessageRole;
  type: MessageType;
  content: string;
  mediaUrl?: string;
  mediaName?: string;
  attachments?: MessageAttachment[];
  tags?: string[] | null;
  isFavorited?: boolean;
  quoteId?: string | null;
  quote?: QuotePreview | null;
  authorAvatarUrl?: string | null;
  authorDisplayName?: string | null;
}

export interface MessageCreate {
  role?: MessageRole;
  type?: MessageType;
  content: string;
  quoteId?: string | null;
}

export interface MessageQuery {
  q?: string;
  tag?: string;
  before?: string;
  after?: string;
  around?: string;
  limit?: number;
}

export interface MessageListResult {
  items: Message[];
  hasMoreBefore: boolean;
  hasMoreAfter: boolean;
  total?: number | null;
  anchorId?: string | null;
}

export interface Persona {
  id: string;
  name: string;
  icon?: string | null;
  systemPrompt: string;
  isBuiltin: boolean;
}

export type AiReviewPeriod = "week" | "month";
