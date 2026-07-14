export type DeepSeekImportMode = "append" | "replace";

export interface DeepSeekSharePreviewItem {
  role: "me" | "ai";
  createdAt: string;
  content: string;
}

export interface DeepSeekSharePreview {
  shareId: string;
  title: string;
  total: number;
  meCount: number;
  aiCount: number;
  rangeFrom: string;
  rangeTo: string;
  preview: DeepSeekSharePreviewItem[];
}

export interface DeepSeekShareImportResult {
  imported: number;
  meCount: number;
  aiCount: number;
  mode: DeepSeekImportMode;
  shareId: string;
  title: string;
}
