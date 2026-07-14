/** 上传与直连 SSE 走直连后端，绕过 dev proxy 缓冲限制 */
export const API_ORIGIN =
  import.meta.env.VITE_API_ORIGIN ?? "http://127.0.0.1:8000";
