<template>
    <div class="skeleton-loader" :class="[`skeleton--${variant}`, className]" :style="customStyle">
        <div class="skeleton-shimmer" />
    </div>
</template>

<script setup lang="ts">
import type { HTMLAttributes } from "vue";

interface Props {
    /** 骨架屏变体 */
    variant?: "text" | "title" | "avatar" | "rect" | "circle" | "button";
    /** 自定义宽度 */
    width?: string;
    /** 自定义高度 */
    height?: string;
    /** 自定义圆角 */
    radius?: string;
    /** 额外 class */
    className?: string;
}

const props = withDefaults(defineProps<Props>(), {
    variant: "text",
});

const customStyle: HTMLAttributes["style"] = {
    width: props.width,
    height: props.height,
    borderRadius: props.radius,
};
</script>

<style scoped>
.skeleton-loader {
    position: relative;
    overflow: hidden;
    background: var(--border);
    border-radius: 4px;
    line-height: 1;
}

.skeleton--text {
    height: 14px;
    width: 100%;
    border-radius: 4px;
}

.skeleton--title {
    height: 20px;
    width: 60%;
    border-radius: 4px;
}

.skeleton--avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    flex-shrink: 0;
}

.skeleton--circle {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    flex-shrink: 0;
}

.skeleton--rect {
    width: 100%;
    height: 80px;
    border-radius: 6px;
}

.skeleton--button {
    width: 80px;
    height: 36px;
    border-radius: 6px;
}

.skeleton-shimmer {
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg,
            transparent 0%,
            rgba(128, 128, 128, 0.08) 50%,
            transparent 100%);
    animation: skeleton-shimmer 1.6s ease-in-out infinite;
    transform: translateX(-100%);
}

@keyframes skeleton-shimmer {
    0% {
        transform: translateX(-100%);
    }

    100% {
        transform: translateX(100%);
    }
}
</style>
