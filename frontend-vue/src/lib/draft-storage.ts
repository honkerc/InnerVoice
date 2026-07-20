// 草稿自动保存：切页 / 刷新不丢失正在写的内容。

const STORAGE_KEY = "yushenduihua-draft";

export function readDraft(): string {
  if (typeof window === "undefined") return "";
  try {
    return localStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

export function writeDraft(value: string): void {
  if (typeof window === "undefined") return;
  try {
    if (value) localStorage.setItem(STORAGE_KEY, value);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore quota / private mode
  }
}

export function clearDraft(): void {
  writeDraft("");
}
