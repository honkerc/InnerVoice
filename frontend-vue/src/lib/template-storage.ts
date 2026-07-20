// 消息模板：常用的记录格式（如日精进），支持 {date} 等占位符，可在设置里管理。

export interface MessageTemplate {
  name: string;
  content: string;
}

const STORAGE_KEY = "custom_templates";

const DEFAULT_TEMPLATES: MessageTemplate[] = [
  {
    name: "日精进",
    content:
      "# 日精进 {date} {weekday}\n\n" +
      "**今日精进**（比昨天做得更好的一件事）\n- \n\n" +
      "**事上磨练**（遇到的人和事 · 我的应对）\n- \n\n" +
      "**自我反省**（哪里可以更好）\n- \n\n" +
      "**明日一件事**\n- [ ] ",
  },
  {
    name: "复盘",
    content:
      "# 复盘 {date}\n\n" +
      "**目标**：今天最重要的一件事是？\n\n" +
      "**结果**：实际做到了什么？\n\n" +
      "**差距**：和预期差在哪，为什么？\n\n" +
      "**改进**：下次怎么做更好？",
  },
  {
    name: "情绪记录",
    content:
      "{datetime} · {weekday}\n\n" +
      "**此刻的感受**：\n\n" +
      "**触发的事**：\n\n" +
      "**身体的反应**：\n\n" +
      "**它想提醒我**：",
  },
  {
    name: "感恩三件事",
    content:
      "# 感恩 {date}\n\n" +
      "1. \n2. \n3. ",
  },
  {
    name: "晨间计划",
    content:
      "# 晨间计划 {date} {weekday}\n\n" +
      "**今天必须完成**\n- [ ] \n\n" +
      "**如果还有余力**\n- [ ] \n\n" +
      "**今天的心态关键词**：",
  },
];

export function readTemplates(): MessageTemplate[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_TEMPLATES.map((t) => ({ ...t }));
    const parsed = JSON.parse(raw);
    if (
      Array.isArray(parsed) &&
      parsed.every(
        (t) => t && typeof t.name === "string" && typeof t.content === "string",
      )
    ) {
      return parsed;
    }
    return DEFAULT_TEMPLATES.map((t) => ({ ...t }));
  } catch {
    return DEFAULT_TEMPLATES.map((t) => ({ ...t }));
  }
}

export function writeTemplates(list: MessageTemplate[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function resetTemplates(): void {
  localStorage.removeItem(STORAGE_KEY);
}

/** 占位符：{date} {time} {datetime} {weekday} {year} {month} {day}，未知的原样保留。 */
export function renderTemplate(content: string): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  const year = now.getFullYear();
  const month = now.getMonth() + 1;
  const day = now.getDate();
  const hh = pad(now.getHours());
  const mm = pad(now.getMinutes());
  const date = `${year}-${pad(month)}-${pad(day)}`;
  const map: Record<string, string> = {
    date,
    time: `${hh}:${mm}`,
    datetime: `${date} ${hh}:${mm}`,
    year: String(year),
    month: String(month),
    day: String(day),
    weekday: `星期${"日一二三四五六"[now.getDay()]}`,
  };
  return content.replace(/\{(\w+)\}/g, (full, key: string) =>
    key in map ? map[key] : full,
  );
}
