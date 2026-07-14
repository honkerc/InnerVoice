import type { AiProvider } from "./settings-types";

export const DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-pro";

export const DEEPSEEK_MODEL_OPTIONS = [
  { value: DEEPSEEK_DEFAULT_MODEL, label: "DeepSeek V4 Pro（推荐）" },
  { value: "deepseek-v4-flash", label: "DeepSeek V4 Flash（更快更省）" },
] as const;

export const AI_PRESETS: Record<
  AiProvider,
  { label: string; baseUrl: string; model: string }
> = {
  deepseek: {
    label: "DeepSeek",
    baseUrl: "https://api.deepseek.com",
    model: DEEPSEEK_DEFAULT_MODEL,
  },
  openai: {
    label: "OpenAI",
    baseUrl: "https://api.openai.com/v1",
    model: "gpt-4o-mini",
  },
  ollama: {
    label: "Ollama（本地）",
    baseUrl: "http://127.0.0.1:11434/v1",
    model: "qwen2.5:7b",
  },
  custom: {
    label: "自定义",
    baseUrl: "",
    model: "",
  },
};

export const AI_PROVIDER_OPTIONS = Object.entries(AI_PRESETS).map(
  ([value, item]) => ({
    value: value as AiProvider,
    label: item.label,
  })
);
