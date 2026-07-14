import type { MessageRole, QuotePreview } from "./types";

export function getQuotedMessageIds(
  messages: { quoteId?: string | null }[]
): Set<string> {
  return new Set(
    messages
      .map((m) => m.quoteId)
      .filter((id): id is string => Boolean(id))
  );
}

export function getQuoteSummary(quote: QuotePreview): string {
  if (quote.type === "media_group") {
    return quote.content.trim() || "附件组";
  }
  if (quote.type === "image") return quote.content || quote.mediaName || "图片";
  if (quote.type === "video") return quote.content || quote.mediaName || "视频";
  if (quote.type === "file") return quote.mediaName || quote.content || "附件";
  const text = quote.content.trim();
  if (!text) return "空消息";
  return text.length > 100 ? `${text.slice(0, 100)}…` : text;
}

export function isAiRole(role: MessageRole): boolean {
  return role === "ai";
}

export function getQuoteLabel(
  quote: QuotePreview,
  aiModelLabel = "AI"
): string {
  if (isAiRole(quote.role)) return aiModelLabel;
  return "我";
}
