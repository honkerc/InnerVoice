// 编辑器内的 “/” 斜杠命令：/ai 呼出 AI 对话，/文字 搜索历史记录。

export type SlashCommand =
  | { kind: "none" }
  | { kind: "menu" } // 仅输入了 “/”
  | { kind: "ai"; question: string }
  | { kind: "search"; query: string };

const AI_COMMAND = /^ai(?:\s+([\s\S]*))?$/i;

export function parseSlash(input: string): SlashCommand {
  if (!input.startsWith("/")) return { kind: "none" };
  // “//” 转义：作为以 / 开头的普通消息，而不是命令
  if (input.startsWith("//")) return { kind: "none" };
  const rest = input.slice(1);
  if (rest.length === 0) return { kind: "menu" };
  const ai = AI_COMMAND.exec(rest);
  if (ai) return { kind: "ai", question: (ai[1] ?? "").trim() };
  return { kind: "search", query: rest.trim() };
}

/** 去掉转义前缀：“//foo” → “/foo”。 */
export function unescapeSlash(input: string): string {
  return input.startsWith("//") ? input.slice(1) : input;
}

export interface SnippetParts {
  pre: string;
  match: string;
  post: string;
}

const SNIPPET_BEFORE = 10;
const SNIPPET_AFTER = 42;

/** 单行片段：命中词居中，前后各留一点上下文。 */
export function buildSnippet(text: string, keyword: string): SnippetParts {
  const flat = text.replace(/\s+/g, " ").trim();
  const idx = keyword ? flat.toLowerCase().indexOf(keyword.toLowerCase()) : -1;
  if (idx < 0) {
    return { pre: flat.slice(0, SNIPPET_BEFORE + SNIPPET_AFTER), match: "", post: "" };
  }
  const start = Math.max(0, idx - SNIPPET_BEFORE);
  const endMatch = idx + keyword.length;
  const end = Math.min(flat.length, endMatch + SNIPPET_AFTER);
  return {
    pre: (start > 0 ? "…" : "") + flat.slice(start, idx),
    match: flat.slice(idx, endMatch),
    post: flat.slice(endMatch, end) + (end < flat.length ? "…" : ""),
  };
}

/** 精简日期：今天只显示时间，本年显示 M月D日，跨年显示 YY/M/D。 */
export function formatShortDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const sameYear = d.getFullYear() === now.getFullYear();
  const sameDay =
    sameYear && d.getMonth() === now.getMonth() && d.getDate() === now.getDate();
  if (sameDay) {
    return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  }
  if (sameYear) return `${d.getMonth() + 1}月${d.getDate()}日`;
  return `${String(d.getFullYear()).slice(2)}/${d.getMonth() + 1}/${d.getDate()}`;
}
