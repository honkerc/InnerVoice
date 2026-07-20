export type AiProvider = "deepseek" | "openai" | "ollama" | "custom";

export interface UserSettings {
  displayName: string;
  avatarUrl?: string | null;
  aiProvider: AiProvider;
  aiModel: string;
  aiBaseUrl: string;
  hasApiKey: boolean;
  aiSystemPrompt: string;
  aiThinking: boolean;
  avatarTransparent: boolean;
  activePersonaId?: string | null;
}

export interface SettingsUpdate {
  displayName?: string;
  avatarUrl?: string | null;
  aiProvider?: AiProvider;
  aiModel?: string;
  aiBaseUrl?: string;
  aiApiKey?: string;
  aiSystemPrompt?: string;
  aiThinking?: boolean;
  avatarTransparent?: boolean;
}
