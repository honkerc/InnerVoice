import type { AiStreamState } from "./ai-content";
import { authFetch } from "./api";
import { API_ORIGIN } from "./api-origin";
import { shouldFlushStreamOnDelta } from "./stream-display";
import type { Message } from "./types";

type SseEvent =
  | { type: "thinking"; delta: string }
  | { type: "content"; delta: string }
  | { type: "done"; message: Message }
  | { type: "error"; error: string };

function parseSseChunk(chunk: string): SseEvent[] {
  const events: SseEvent[] = [];
  for (const block of chunk.split("\n\n")) {
    for (const line of block.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const payload = trimmed.slice(5).trim();
      if (!payload) continue;
      try {
        const raw = JSON.parse(payload) as Record<string, unknown>;
        if (raw.type === "thinking" && typeof raw.delta === "string") {
          events.push({ type: "thinking", delta: raw.delta });
        } else if (raw.type === "content" && typeof raw.delta === "string") {
          events.push({ type: "content", delta: raw.delta });
        } else if (raw.type === "done" && raw.message) {
          events.push({ type: "done", message: raw.message as Message });
        } else if (raw.type === "error") {
          events.push({
            type: "error",
            error: typeof raw.error === "string" ? raw.error : "AI 回复失败",
          });
        }
      } catch {
        // ignore malformed chunk
      }
    }
  }
  return events;
}

export interface StreamAiReplyHandlers {
  onStart?: () => void;
  onUpdate: (state: AiStreamState) => void;
  onDone: (message: Message) => void;
  onError: (message: string) => void;
}

/** 经 Next Route Handler 透传 SSE（同源、不缓冲） */
export async function streamAiReply(
  triggerMessageId: string,
  force: boolean,
  handlers: StreamAiReplyHandlers,
  signal?: AbortSignal
): Promise<void> {
  let res: Response;
  try {
    res = await authFetch(`${API_ORIGIN}/api/messages/ai-reply/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ triggerMessageId, force }),
      signal,
    });
  } catch (err) {
    if (signal?.aborted) return;
    handlers.onError(err instanceof Error ? err.message : "AI 连接失败");
    return;
  }

  if (!res.ok) {
    let message = "AI 回复失败";
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
    } catch {
      // ignore
    }
    handlers.onError(message);
    return;
  }

  if (!res.body) {
    handlers.onError("AI 流式响应为空");
    return;
  }

  handlers.onStart?.();

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let thinking = "";
  let answer = "";
  let phase: AiStreamState["phase"] = "thinking";
  let finished = false;

  const pushUpdate = () => {
    handlers.onUpdate({ thinking, answer, phase });
  };

  const handleEvent = (event: SseEvent): boolean => {
    if (event.type === "thinking") {
      thinking += event.delta;
      phase = "thinking";
      if (shouldFlushStreamOnDelta(event.delta)) pushUpdate();
      return false;
    }
    if (event.type === "content") {
      const phaseChanged = phase === "thinking";
      answer += event.delta;
      phase = "answer";
      if (phaseChanged || shouldFlushStreamOnDelta(event.delta)) pushUpdate();
      return false;
    }
    if (event.type === "done") {
      finished = true;
      handlers.onDone(event.message);
      return true;
    }
    finished = true;
    handlers.onError(event.error);
    return true;
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const splitAt = buffer.lastIndexOf("\n\n");
      if (splitAt === -1) continue;

      const chunk = buffer.slice(0, splitAt + 2);
      buffer = buffer.slice(splitAt + 2);

      for (const event of parseSseChunk(chunk)) {
        if (handleEvent(event)) return;
      }
    }

    if (buffer.trim()) {
      for (const event of parseSseChunk(buffer)) {
        if (handleEvent(event)) return;
      }
    }

    if (!finished) {
      handlers.onError("AI 回复中断，请重试");
    }
  } catch (err) {
    if (!signal?.aborted && !finished) {
      handlers.onError(err instanceof Error ? err.message : "AI 流式读取失败");
    }
  }
}
