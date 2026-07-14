<template>
    <div class="chat-skeleton">
        <!-- 我 -->
        <div class="chat-skeleton__row chat-skeleton__row--right">
            <SkeletonLoader variant="avatar" />
            <div class="chat-skeleton__lines chat-skeleton__lines--right">
                <SkeletonLoader variant="text" width="140px" />
                <SkeletonLoader variant="text" width="100px" />
            </div>
        </div>

        <!-- AI 长回复 -->
        <div class="chat-skeleton__row chat-skeleton__row--left chat-skeleton__row--long">
            <SkeletonLoader variant="avatar" />
            <div class="chat-skeleton__lines chat-skeleton__lines--left chat-skeleton__lines--long">
                <SkeletonLoader variant="title" width="75%" />
                <SkeletonLoader variant="text" width="100%" />
                <SkeletonLoader variant="text" width="100%" />
                <SkeletonLoader variant="text" width="85%" />
                <SkeletonLoader variant="rect" width="100%" height="200px" />
                <SkeletonLoader variant="text" width="100%" />
                <SkeletonLoader variant="text" width="90%" />
                <SkeletonLoader variant="text" width="60%" />
            </div>
        </div>

        <!-- 我 -->
        <div class="chat-skeleton__row chat-skeleton__row--right">
            <SkeletonLoader variant="avatar" />
            <div class="chat-skeleton__lines chat-skeleton__lines--right">
                <SkeletonLoader variant="text" width="180px" />
                <SkeletonLoader variant="text" width="90px" />
            </div>
        </div>

        <!-- AI -->
        <div class="chat-skeleton__row chat-skeleton__row--left chat-skeleton__row--long">
            <SkeletonLoader variant="avatar" />
            <div class="chat-skeleton__lines chat-skeleton__lines--left chat-skeleton__lines--long">
                <SkeletonLoader variant="text" width="100%" />
                <SkeletonLoader variant="text" width="95%" />
                <SkeletonLoader variant="text" width="50%" />
                <SkeletonLoader variant="rect" width="100%" height="160px" />
                <SkeletonLoader variant="text" width="100%" />
                <SkeletonLoader variant="text" width="80%" />
            </div>
        </div>

        <!-- 我 -->
        <div class="chat-skeleton__row chat-skeleton__row--right">
            <SkeletonLoader variant="avatar" />
            <div class="chat-skeleton__lines chat-skeleton__lines--right">
                <SkeletonLoader variant="text" width="120px" />
                <SkeletonLoader variant="text" width="70px" />
            </div>
        </div>

        <!-- AI -->
        <div class="chat-skeleton__row chat-skeleton__row--left chat-skeleton__row--long">
            <SkeletonLoader variant="avatar" />
            <div class="chat-skeleton__lines chat-skeleton__lines--left chat-skeleton__lines--long">
                <SkeletonLoader variant="title" width="60%" />
                <SkeletonLoader variant="text" width="100%" />
                <SkeletonLoader variant="text" width="100%" />
                <SkeletonLoader variant="text" width="80%" />
                <SkeletonLoader variant="rect" width="100%" height="60px" />
                <SkeletonLoader variant="text" width="100%" />
                <SkeletonLoader variant="text" width="65%" />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import SkeletonLoader from "./SkeletonLoader.vue";
</script>

<style scoped>
.chat-skeleton {
    display: flex;
    flex-direction: column;
    gap: 24px;
    width: 100%;
    min-width: 0;
    max-width: 100%;
    padding: var(--layout-padding) var(--layout-padding) 0;
}

.chat-skeleton__row {
    display: flex;
    gap: 10px;
    width: fit-content;
    min-width: 0;
    max-width: 80%;
}

.chat-skeleton__row--right {
    align-self: flex-end;
    flex-direction: row-reverse;
}

.chat-skeleton__row--left {
    align-self: flex-start;
    flex-direction: row;
}

.chat-skeleton__row--long {
    max-width: 70%;
    width: 70%;
}

.chat-skeleton__lines {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 120px;
    flex: 1;
}

.chat-skeleton__lines--right {
    align-items: flex-end;
}

.chat-skeleton__lines--left {
    align-items: flex-start;
}

.chat-skeleton__lines--long {
    width: 100%;
}
</style>
