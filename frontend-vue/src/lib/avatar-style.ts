// 头像透明背景：开启后把前端头像的背景填充置空（body 上挂一个类，CSS 兜底）。

export function applyAvatarTransparency(enabled: boolean): void {
  if (typeof document === "undefined") return;
  document.body.classList.toggle("avatar-transparent", !!enabled);
}
