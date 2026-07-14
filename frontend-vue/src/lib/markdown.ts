import { Marked, Renderer } from "marked";
import hljs from "highlight.js/lib/core";
import bash from "highlight.js/lib/languages/bash";
import c from "highlight.js/lib/languages/c";
import cpp from "highlight.js/lib/languages/cpp";
import csharp from "highlight.js/lib/languages/csharp";
import css from "highlight.js/lib/languages/css";
import go from "highlight.js/lib/languages/go";
import java from "highlight.js/lib/languages/java";
import javascript from "highlight.js/lib/languages/javascript";
import json from "highlight.js/lib/languages/json";
import kotlin from "highlight.js/lib/languages/kotlin";
import markdownLang from "highlight.js/lib/languages/markdown";
import php from "highlight.js/lib/languages/php";
import python from "highlight.js/lib/languages/python";
import rust from "highlight.js/lib/languages/rust";
import shell from "highlight.js/lib/languages/shell";
import sql from "highlight.js/lib/languages/sql";
import swift from "highlight.js/lib/languages/swift";
import typescript from "highlight.js/lib/languages/typescript";
import xml from "highlight.js/lib/languages/xml";
import yaml from "highlight.js/lib/languages/yaml";

const languages: Array<[string, Parameters<typeof hljs.registerLanguage>[1]]> = [
  ["bash", bash],
  ["c", c],
  ["cpp", cpp],
  ["csharp", csharp],
  ["css", css],
  ["go", go],
  ["html", xml],
  ["java", java],
  ["javascript", javascript],
  ["json", json],
  ["kotlin", kotlin],
  ["markdown", markdownLang],
  ["php", php],
  ["python", python],
  ["rust", rust],
  ["shell", shell],
  ["sh", bash],
  ["sql", sql],
  ["swift", swift],
  ["ts", typescript],
  ["typescript", typescript],
  ["xml", xml],
  ["yaml", yaml],
];

for (const [name, language] of languages) {
  hljs.registerLanguage(name, language);
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const renderer = new Renderer();
renderer.code = function ({ text, lang }) {
  const language = (lang || "").trim().toLowerCase();
  let highlighted = escapeHtml(text);
  let resolvedLanguage = "";

  if (language && hljs.getLanguage(language)) {
    try {
      highlighted = hljs.highlight(text, { language }).value;
      resolvedLanguage = language;
    } catch {
      highlighted = escapeHtml(text);
    }
  }

  const langAttr = resolvedLanguage ? ` data-language="${resolvedLanguage}"` : "";
  const codeClass = resolvedLanguage ? `hljs language-${resolvedLanguage}` : "hljs";
  return `<pre${langAttr}><code class="${codeClass}">${highlighted}</code></pre>`;
};

const marked = new Marked({
  renderer,
  breaks: true,
  gfm: true,
});

export function renderMarkdown(content: string): string {
  if (!content.trim()) return "";
  try {
    return marked.parse(content, { async: false }) as string;
  } catch {
    return escapeHtml(content);
  }
}
