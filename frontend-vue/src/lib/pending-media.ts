export type PendingMediaKind = "image" | "video" | "file";

export interface PendingMedia {
  id: string;
  file: File;
  kind: PendingMediaKind;
  previewUrl?: string;
  name: string;
}

const IMAGE_EXTENSIONS = new Set([
  ".jpg",
  ".jpeg",
  ".png",
  ".gif",
  ".webp",
  ".bmp",
  ".heic",
  ".heif",
]);

const VIDEO_EXTENSIONS = new Set([".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v"]);

function extOf(name: string): string {
  return name.includes(".") ? name.slice(name.lastIndexOf(".")).toLowerCase() : "";
}

export function isImageFile(file: File): boolean {
  if (file.type.startsWith("image/")) return true;
  return IMAGE_EXTENSIONS.has(extOf(file.name));
}

export function isVideoFile(file: File): boolean {
  if (file.type.startsWith("video/")) return true;
  return VIDEO_EXTENSIONS.has(extOf(file.name));
}

export function detectKind(file: File): PendingMediaKind {
  if (isImageFile(file)) return "image";
  if (isVideoFile(file)) return "video";
  return "file";
}

function makeId(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `media-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function createPendingMedia(file: File): PendingMedia {
  const kind = detectKind(file);
  return {
    id: makeId(),
    file,
    kind,
    previewUrl: kind === "image" || kind === "video" ? URL.createObjectURL(file) : undefined,
    name: file.name,
  };
}

export function revokePendingMedia(item: PendingMedia) {
  if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
}

export function revokeAllPendingMedia(items: PendingMedia[]) {
  items.forEach(revokePendingMedia);
}
