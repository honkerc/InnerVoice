import { parseAiContent, type AiStreamState } from "./ai-content";
import { isAiRole } from "./quote";
import type { Message } from "./types";

export function getMessageCopyText(message: Message): string {
  if (message.type === "text") {
    if (isAiRole(message.role)) {
      const { thinking, answer } = parseAiContent(message.content);
      return (answer || thinking).trim();
    }
    return message.content.trim();
  }

  if (message.type === "image" || message.type === "video") {
    return message.content.trim() || message.mediaName || "";
  }

  if (message.type === "file") {
    return message.mediaName || message.content || message.mediaUrl || "";
  }

  if (message.type === "media_group") {
    const names = message.attachments?.map((item) => item.name).filter(Boolean) ?? [];
    return message.content.trim() || names.join("\n");
  }

  return message.content.trim();
}

export function getStreamCopyText(stream: AiStreamState): string {
  const answer = stream.answer.trim();
  const thinking = stream.thinking.trim();
  return answer || thinking;
}
