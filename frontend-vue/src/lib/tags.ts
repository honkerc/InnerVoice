export function stripKnownTags(content: string, tags?: string[] | null): string {
  if (!tags?.length) return content;
  let result = content;
  for (const tag of tags) {
    const escaped = tag.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    result = result.replace(new RegExp(`[ \\t]?#${escaped}(?=[\\s#]|$)`, "gu"), "");
  }
  return result.replace(/\n{3,}/g, "\n\n").trim();
}
