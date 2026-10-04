<template>
  <view class="section-header" :class="{ 'section-header--flush': scrollPadding }">
    <text class="section-header__title">{{ title }}</text>
    <text v-if="more" class="section-header__more" @tap="$emit('more')">{{ more }} ›</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 分区大标题。
 *
 * 刻意没有装饰条 —— 旧版的「│ 小暖推荐」（4px 竖色条）被删掉了。
 * 层级靠字号(36rpx)和字重(700)建立，这是素材的做法（spec §3.5）。
 *
 * scrollPadding=true 时不加左右内边距，交给调用方 —— 横滑区的标题
 * 要和卡片左对齐，而卡片的滚动容器自带 padding。
 */
defineProps<{
  title: string
  more?: string
  scrollPadding?: boolean
}>()

defineEmits<{ more: [] }>()
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: var(--space-xl) var(--space-lg) var(--space-md);
}

.section-header--flush {
  padding-left: 0;
  padding-right: 0;
}

.section-header__title {
  font-size: var(--font-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  line-height: var(--leading-tight);
}

.section-header__more {
  font-size: var(--font-sm);
  color: var(--text-muted);
}
</style>
