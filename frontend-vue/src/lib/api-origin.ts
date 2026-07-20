/** 上传与直连 SSE 走直连后端，绕过 dev proxy 缓冲限制。
 * 生产环境未显式配置 VITE_API_ORIGIN 时退回同源相对路径，
 * 避免打包后仍指向仅开发环境可用的 127.0.0.1:8000。 */
export const API_ORIGIN =
  import.meta.env.VITE_API_ORIGIN ?? (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");
