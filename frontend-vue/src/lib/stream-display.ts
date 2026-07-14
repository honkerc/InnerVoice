/** 流式展示：只显示已完整的行（遇到换行才算一行结束） */
export function visibleStreamingLines(text: string): string {
  const idx = text.lastIndexOf("\n");
  if (idx === -1) return "";
  return text.slice(0, idx + 1);
}

export function shouldFlushStreamOnDelta(delta: string): boolean {
  return delta.includes("\n");
}

export function splitDisplayLines(text: string): string[] {
  if (!text) return [];
  const lines = text.split("\n");
  if (lines.length > 0 && lines[lines.length - 1] === "") {
    lines.pop();
  }
  return lines;
}
