const STORAGE_KEY = "custom_emoji_list";

const DEFAULT_EMOJIS = [
    "😀", "😂", "🥹", "😊", "😍", "🤔", "😭", "😡",
    "👍", "🙏", "💪", "✨", "🔥", "❤️", "🌙", "☀️",
    "📝", "💡", "🎯", "🌱", "🕊️", "🙌", "👀", "💭",
];

export function readEmojiList(): string[] {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return [...DEFAULT_EMOJIS];
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.every((e) => typeof e === "string")) {
            return parsed;
        }
        return [...DEFAULT_EMOJIS];
    } catch {
        return [...DEFAULT_EMOJIS];
    }
}

export function writeEmojiList(list: string[]): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function resetEmojiList(): void {
    localStorage.removeItem(STORAGE_KEY);
}
