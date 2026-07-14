import { onUnmounted, ref, watch } from "vue";

const BASE_CHAR_MS = 34;

const CHAR_PAUSE_MS: Record<string, number> = {
  "。": 160,
  "！": 160,
  "？": 160,
  "；": 130,
  "…": 120,
  "，": 78,
  "、": 78,
  "：": 78,
  "\n": 100,
};

function pauseForChar(char: string): number {
  return CHAR_PAUSE_MS[char] ?? BASE_CHAR_MS;
}

/** 将目标文本以接近人眼阅读的速度逐字展开，避免整行瞬间弹出。 */
export function useRevealingText(target: () => string, active: () => boolean) {
  const revealed = ref("");
  const revealedValue = ref("");
  let timer: ReturnType<typeof setTimeout> | null = null;

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function sync(targetText: string, isActive: boolean) {
    clearTimer();

    if (!isActive) {
      revealed.value = targetText;
      revealedValue.value = targetText;
      return;
    }

    if (targetText.length < revealedValue.value.length) {
      revealed.value = targetText;
      revealedValue.value = targetText;
    }

    const step = () => {
      const current = revealedValue.value;
      if (current.length >= targetText.length) return;

      const nextLen = current.length + 1;
      const next = targetText.slice(0, nextLen);
      revealedValue.value = next;
      revealed.value = next;

      const ch = targetText[nextLen - 1] ?? "";
      timer = setTimeout(step, pauseForChar(ch));
    };

    if (revealedValue.value.length < targetText.length) {
      step();
    }
  }

  watch(
    () => [target(), active()] as const,
    ([targetText, isActive]) => sync(targetText, isActive),
    { immediate: true },
  );

  onUnmounted(clearTimer);

  return revealed;
}
