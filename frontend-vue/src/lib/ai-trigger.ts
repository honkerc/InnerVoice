const AI_MENTION = /\B@ai\b/i;

export function shouldInvokeAi(text: string): boolean {
  return AI_MENTION.test(text);
}

export function shouldCallAi(text: string, toolbarEnabled: boolean): boolean {
  return toolbarEnabled || shouldInvokeAi(text);
}
