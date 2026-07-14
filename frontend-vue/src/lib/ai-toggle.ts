const STORAGE_KEY = "yushenduihua-ai-enabled";

export function readAiEnabled(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === null) return false;
    return value === "1";
  } catch {
    return false;
  }
}

export function writeAiEnabled(enabled: boolean): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, enabled ? "1" : "0");
  } catch {
    // ignore quota / private mode
  }
}
