export const AI_THINKING_START = "<!--ai-thinking-->";
export const AI_THINKING_END = "<!--/ai-thinking-->";

export interface ParsedAiContent {
  thinking: string;
  answer: string;
}

export function formatAiContent(thinking: string, answer: string): string {
  const t = thinking.trim();
  let a = answer.trim();
  if (!a && t) {
    a = t;
    return a;
  }
  if (t) {
    return `${AI_THINKING_START}\n${t}\n${AI_THINKING_END}\n\n${a}`;
  }
  return a;
}

export function parseAiContent(content: string): ParsedAiContent {
  const start = content.indexOf(AI_THINKING_START);
  const end = content.indexOf(AI_THINKING_END);
  if (start === -1 || end === -1 || end < start) {
    return { thinking: "", answer: content.trim() };
  }
  const thinking = content
    .slice(start + AI_THINKING_START.length, end)
    .trim();
  const answer = content.slice(end + AI_THINKING_END.length).trim();
  return { thinking, answer };
}

export interface AiStreamState {
  thinking: string;
  answer: string;
  phase: "thinking" | "answer";
}
