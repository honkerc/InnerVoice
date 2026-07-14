export function formatAiModelLabel(model?: string | null): string {
  const name = model?.trim();
  if (!name) return "AI";
  return name.length > 28 ? `${name.slice(0, 28)}…` : name;
}

export function aiMetaLabel(model: string | undefined, suffix: string): string {
  return `${formatAiModelLabel(model)} · ${suffix}`;
}
