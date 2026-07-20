// 主题切换：light（妖艳红）/ dark（黑金）。挂在 <html data-theme> 上，CSS 变量随之切换。

export type Theme = "light" | "dark";

const STORAGE_KEY = "yushenduihua-theme";

function readStored(): Theme | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v === "light" || v === "dark" ? v : null;
  } catch {
    return null;
  }
}

export function systemTheme(): Theme {
  if (typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

export function currentTheme(): Theme {
  if (typeof document === "undefined") return "light";
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

export function applyTheme(theme: Theme, persist = true): void {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
  if (persist) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // ignore
    }
  }
}

/** 应用启动时调用：优先用户选择，否则跟随系统（不写入存储）。 */
export function initTheme(): void {
  const stored = readStored();
  applyTheme(stored ?? systemTheme(), stored !== null);
}

export function toggleTheme(): Theme {
  const next: Theme = currentTheme() === "dark" ? "light" : "dark";
  applyTheme(next);
  return next;
}
