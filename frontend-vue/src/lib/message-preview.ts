import type { Message } from "./types";
import { getQuoteSummary } from "./quote";
import type { QuotePreview } from "./types";

export function getMessagePreviewText(message: Pick<Message, "type" | "content" | "mediaName">): string {
  const quoteLike: QuotePreview = {
    id: "",
    role: "me",
    type: message.type,
    content: message.content,
    mediaName: message.mediaName,
  };
  return getQuoteSummary(quoteLike);
}
