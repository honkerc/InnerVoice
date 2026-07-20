import { API_ORIGIN } from "./api-origin";
import {
  authHeaders,
  clearAuthTokens,
  readRefreshToken,
  saveAuthTokens,
  type AuthTokens,
} from "./auth";
import type {
  AiReviewPeriod,
  Message,
  MessageCreate,
  MessageListResult,
  MessageQuery,
  Persona,
} from "./types";
import type { SettingsUpdate, UserSettings } from "./settings-types";
import type { DeepSeekShareImportResult, DeepSeekSharePreview, DeepSeekImportMode } from "./import-types";

function extractErrorDetail(data: unknown, fallback: string): string {
  if (typeof data !== "object" || data === null || !("detail" in data)) {
    return fallback;
  }
  const detail = (data as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === "object" && first !== null && "msg" in first) {
      return String((first as { msg: unknown }).msg);
    }
  }
  return fallback;
}

async function parseError(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    return extractErrorDetail(data, fallback);
  } catch {
    return fallback;
  }
}

async function parseErrorBody(body: string, fallback: string): Promise<string> {
  if (!body.trim()) return fallback;
  try {
    const data = JSON.parse(body);
    if (typeof data.detail === "string") return data.detail;
    return fallback;
  } catch {
    return fallback;
  }
}

let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = readRefreshToken();
  if (!refreshToken) return false;

  const res = await fetch("/api/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refreshToken }),
  });

  if (!res.ok) {
    clearAuthTokens();
    return false;
  }

  const tokens = (await res.json()) as AuthTokens;
  saveAuthTokens(tokens);
  return true;
}

async function ensureRefreshed(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

function redirectToLogin() {
  if (typeof window === "undefined") return;
  if (window.location.pathname === "/login") return;
  clearAuthTokens();
  window.location.href = "/login";
}

export async function authFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
  retry = true
): Promise<Response> {
  const headers = new Headers(init.headers);
  const auth = authHeaders();
  Object.entries(auth).forEach(([key, value]) => headers.set(key, value));

  const res = await fetch(input, { ...init, headers });

  if (res.status !== 401 || !retry) {
    return res;
  }

  const refreshed = await ensureRefreshed();
  if (!refreshed) {
    redirectToLogin();
    return res;
  }

  const retryHeaders = new Headers(init.headers);
  Object.entries(authHeaders()).forEach(([key, value]) =>
    retryHeaders.set(key, value)
  );
  return fetch(input, { ...init, headers: retryHeaders });
}

export async function login(
  username: string,
  password: string
): Promise<AuthTokens> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(await parseError(res, "登录失败"));
  const tokens = (await res.json()) as AuthTokens;
  saveAuthTokens(tokens);
  return tokens;
}

export async function changeUsername(
  newUsername: string
): Promise<{ username: string }> {
  const res = await authFetch("/api/auth/change-username", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ newUsername }),
  });
  if (!res.ok) throw new Error(await parseError(res, "修改用户名失败"));
  return res.json();
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<void> {
  const res = await authFetch("/api/auth/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ currentPassword, newPassword }),
  });
  if (!res.ok) throw new Error(await parseError(res, "修改密码失败"));
  clearAuthTokens();
}

export async function fetchMessages(
  query: MessageQuery = {}
): Promise<MessageListResult> {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.tag) params.set("tag", query.tag);
  if (query.before) params.set("before", query.before);
  if (query.after) params.set("after", query.after);
  if (query.around) params.set("around", query.around);
  if (query.limit) params.set("limit", String(query.limit));
  const qs = params.toString();
  const res = await authFetch(`/api/messages${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error("加载消息失败");
  return res.json();
}

export async function fetchMessage(id: string): Promise<Message | null> {
  const res = await authFetch(`/api/messages/${encodeURIComponent(id)}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("加载消息失败");
  return res.json();
}

export async function sendTextMessage(data: MessageCreate): Promise<Message> {
  const res = await authFetch("/api/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role: "me", type: "text", ...data }),
  });
  if (!res.ok) throw new Error(await parseError(res, "发送失败"));
  return res.json();
}

export async function requestAiReply(
  triggerMessageId: string,
  force = false
): Promise<Message> {
  const res = await authFetch(`${API_ORIGIN}/api/messages/ai-reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ triggerMessageId, force }),
  });
  if (!res.ok) {
    throw new Error(
      await parseError(
        res,
        res.status === 502
          ? "AI 调用失败，请检查后端 AI_API_KEY 环境变量与余额，并确认后端已重启"
          : "AI 回复失败"
      )
    );
  }
  return res.json();
}

export function sendMediaMessage(
  files: File[],
  content = "",
  quoteId?: string | null,
  onProgress?: (loaded: number, total: number) => void
): Promise<Message> {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  form.append("content", content);
  form.append("role", "me");
  if (quoteId) form.append("quote_id", quoteId);

  const totalSize = files.reduce((sum, file) => sum + file.size, 0);
  const token = authHeaders().Authorization;

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_ORIGIN}/api/messages/media`);
    if (token) xhr.setRequestHeader("Authorization", token);

    xhr.upload.onprogress = (event) => {
      if (!onProgress) return;
      onProgress(
        event.loaded,
        event.lengthComputable ? event.total : totalSize
      );
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as Message);
        } catch {
          reject(new Error("上传失败"));
        }
        return;
      }
      if (xhr.status === 401) {
        ensureRefreshed()
          .then((ok) => {
            if (!ok) {
              redirectToLogin();
              reject(new Error("登录已过期"));
              return;
            }
            sendMediaMessage(files, content, quoteId, onProgress)
              .then(resolve)
              .catch(reject);
          })
          .catch(reject);
        return;
      }
      parseErrorBody(xhr.responseText, "上传失败").then((msg) =>
        reject(new Error(msg))
      );
    };

    xhr.onerror = () =>
      reject(new Error("无法连接后端，请确认 8000 端口服务已启动"));
    xhr.send(form);
  });
}

export async function editMessage(id: string, content: string): Promise<Message> {
  const res = await authFetch(`/api/messages/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(await parseError(res, "修改失败"));
  return res.json();
}

export async function deleteMessage(id: string): Promise<void> {
  const res = await authFetch(`/api/messages/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("删除失败");
}

export async function fetchFavorites(): Promise<Message[]> {
  const res = await authFetch("/api/favorites");
  if (!res.ok) throw new Error("加载收藏失败");
  return res.json();
}

export async function favoriteMessage(id: string): Promise<Message> {
  const res = await authFetch(`/api/messages/${encodeURIComponent(id)}/favorite`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await parseError(res, "收藏失败"));
  return res.json();
}

export async function unfavoriteMessage(id: string): Promise<Message> {
  const res = await authFetch(`/api/messages/${encodeURIComponent(id)}/favorite`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await parseError(res, "取消收藏失败"));
  return res.json();
}

export async function fetchMessagesNearDate(date: string): Promise<MessageListResult> {
  const res = await authFetch(`/api/messages/near-date?date=${encodeURIComponent(date)}`);
  if (!res.ok) throw new Error(await parseError(res, "跳转失败"));
  return res.json();
}

export async function requestAiReview(period: AiReviewPeriod): Promise<Message> {
  const res = await authFetch("/api/messages/ai-review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ period }),
  });
  if (!res.ok) throw new Error(await parseError(res, "生成回顾失败"));
  return res.json();
}

export async function fetchPersonas(): Promise<Persona[]> {
  const res = await authFetch("/api/personas");
  if (!res.ok) throw new Error("加载人格失败");
  return res.json();
}

export async function createPersona(data: {
  name: string;
  icon?: string | null;
  systemPrompt?: string;
}): Promise<Persona> {
  const res = await authFetch("/api/personas", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseError(res, "新增人格失败"));
  return res.json();
}

export async function updatePersona(
  id: string,
  data: { name?: string; icon?: string | null; systemPrompt?: string }
): Promise<Persona> {
  const res = await authFetch(`/api/personas/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseError(res, "保存人格失败"));
  return res.json();
}

export async function deletePersona(id: string): Promise<void> {
  const res = await authFetch(`/api/personas/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await parseError(res, "删除人格失败"));
}

export async function setActivePersona(personaId: string | null): Promise<UserSettings> {
  const res = await authFetch("/api/settings/persona", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ personaId }),
  });
  if (!res.ok) throw new Error(await parseError(res, "切换人格失败"));
  return res.json();
}

export async function exportMessages(format: "md" | "json"): Promise<void> {
  const res = await authFetch(`/api/export?format=${format}`);
  if (!res.ok) throw new Error(await parseError(res, "导出失败"));
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : `export.${format}`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function fetchSettings(): Promise<UserSettings> {
  const res = await authFetch("/api/settings");
  if (!res.ok) throw new Error("加载设置失败");
  return res.json();
}

export async function saveSettings(data: SettingsUpdate): Promise<UserSettings> {
  const res = await authFetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseError(res, "保存失败"));
  return res.json();
}

export async function uploadAvatar(file: File): Promise<UserSettings> {
  const form = new FormData();
  form.append("file", file);
  const res = await authFetch(`${API_ORIGIN}/api/settings/avatar`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await parseError(res, "头像上传失败"));
  return res.json();
}

export async function removeAvatar(): Promise<UserSettings> {
  const res = await authFetch(`${API_ORIGIN}/api/settings/avatar`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await parseError(res, "删除头像失败"));
  return res.json();
}

export async function previewDeepSeekShare(url: string): Promise<DeepSeekSharePreview> {
  const res = await authFetch("/api/import/deepseek-share/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error(await parseError(res, "预览失败"));
  return res.json();
}

export async function importDeepSeekShare(
  url: string,
  mode: DeepSeekImportMode = "append"
): Promise<DeepSeekShareImportResult> {
  const res = await authFetch("/api/import/deepseek-share", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, mode }),
  });
  if (!res.ok) throw new Error(await parseError(res, "导入失败"));
  return res.json();
}

export { authHeaders };
