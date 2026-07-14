export interface PendingImage {
  id: string;
  file: File;
  previewUrl: string;
  name: string;
}

export function createPendingImage(file: File): PendingImage {
  return {
    id:
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `img-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    file,
    previewUrl: URL.createObjectURL(file),
    name: file.name,
  };
}

export function revokePendingImage(item: PendingImage) {
  URL.revokeObjectURL(item.previewUrl);
}

export function revokeAllPendingImages(items: PendingImage[]) {
  items.forEach(revokePendingImage);
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

export function isImageFile(file: File): boolean {
  if (file.type.startsWith("image/")) return true;
  const ext = file.name.includes(".")
    ? file.name.slice(file.name.lastIndexOf(".")).toLowerCase()
    : "";
  return IMAGE_EXTENSIONS.has(ext);
}
