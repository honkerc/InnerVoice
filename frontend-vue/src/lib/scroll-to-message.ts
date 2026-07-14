export function scrollToMessage(
  messageId: string,
  behavior: ScrollBehavior = "smooth"
): boolean {
  const el = document.getElementById(`message-${messageId}`);
  if (!el) return false;
  el.scrollIntoView({ behavior, block: "center" });
  return true;
}
