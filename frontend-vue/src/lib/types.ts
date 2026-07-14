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
