<template>
    <div class="settings-skeleton">
        <!-- 头部骨架 -->
        <div class="settings-skeleton__header">
            <SkeletonLoader variant="title" width="80px" />
            <SkeletonLoader variant="circle" width="32px" height="32px" />
        </div>

        <!-- 个人资料卡片骨架 -->
        <div class="settings-skeleton__card">
            <div class="settings-skeleton__grid">
                <div class="settings-skeleton__col">
                    <SkeletonLoader variant="title" width="100px" />
                    <SkeletonLoader variant="text" width="180px" class="settings-skeleton__mt-sm" />
                    <SkeletonLoader variant="rect" width="100%" height="200px" class="settings-skeleton__mt-md" />
                    <SkeletonLoader variant="text" width="100%" class="settings-skeleton__mt-md" />
                    <SkeletonLoader variant="text" width="100%" />
                </div>
                <div class="settings-skeleton__col">
                    <SkeletonLoader variant="title" width="60px" />
                    <SkeletonLoader variant="text" width="200px" class="settings-skeleton__mt-sm" />
                    <div class="settings-skeleton__fields">
                        <SkeletonLoader variant="rect" width="100%" height="38px" />
                        <SkeletonLoader variant="rect" width="100%" height="38px" />
                        <SkeletonLoader variant="rect" width="100%" height="38px" />
                    </div>
                    <div class="settings-skeleton__actions">
                        <SkeletonLoader variant="button" width="100px" />
                        <SkeletonLoader variant="button" width="80px" />
                    </div>
                </div>
            </div>
        </div>

        <!-- AI 设置卡片骨架 -->
        <div class="settings-skeleton__card">
            <SkeletonLoader variant="title" width="60px" />
            <SkeletonLoader variant="text" width="240px" class="settings-skeleton__mt-sm" />
            <div class="settings-skeleton__fields">
                <SkeletonLoader variant="rect" width="100%" height="38px" />
                <SkeletonLoader variant="rect" width="100%" height="38px" />
                <SkeletonLoader variant="rect" width="100%" height="38px" />
                <SkeletonLoader variant="rect" width="100%" height="38px" />
                <SkeletonLoader variant="rect" width="100%" height="120px" />
            </div>
        </div>

        <!-- 导入卡片骨架 -->
        <div class="settings-skeleton__card">
            <SkeletonLoader variant="title" width="160px" />
            <SkeletonLoader variant="text" width="300px" class="settings-skeleton__mt-sm" />
            <div class="settings-skeleton__fields">
                <SkeletonLoader variant="rect" width="100%" height="38px" />
                <SkeletonLoader variant="rect" width="100%" height="38px" />
            </div>
            <div class="settings-skeleton__actions">
                <SkeletonLoader variant="button" width="80px" />
                <SkeletonLoader variant="button" width="100px" />
            </div>
        </div>

        <!-- 保存按钮骨架 -->
        <SkeletonLoader variant="button" width="100%" height="42px" />
    </div>
</template>

<script setup lang="ts">
import SkeletonLoader from "./SkeletonLoader.vue";
</script>

<style scoped>
.settings-skeleton {
    width: 100%;
    max-width: var(--layout-width);
    margin: 0 auto;
    padding: 20px 16px 48px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.settings-skeleton__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 48px;
    padding: 0 var(--layout-padding);
}

.settings-skeleton__card {
    padding: 24px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
}

.settings-skeleton__grid {
    display: grid;
    grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
    gap: 28px;
    align-items: start;
}

.settings-skeleton__col {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.settings-skeleton__fields {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 20px;
}

.settings-skeleton__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
}

.settings-skeleton__mt-sm {
    margin-top: 4px;
}

.settings-skeleton__mt-md {
    margin-top: 14px;
}

@media (max-width: 860px) {
    .settings-skeleton__grid {
        grid-template-columns: 1fr;
        gap: 24px;
    }
}
</style>
