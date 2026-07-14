/** 合并高频流式更新，避免逐字触发重渲染 */
export function createStreamScheduler(onFlush: () => void, intervalMs = 48) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let dirty = false;

  const markDirty = () => {
    dirty = true;
    if (timer !== null) return;
    timer = setTimeout(() => {
      timer = null;
      if (!dirty) return;
      dirty = false;
      onFlush();
    }, intervalMs);
  };

  const flush = () => {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
    if (!dirty) return;
    dirty = false;
    onFlush();
  };

  const cancel = () => {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
    dirty = false;
  };

  return { markDirty, flush, cancel };
}
