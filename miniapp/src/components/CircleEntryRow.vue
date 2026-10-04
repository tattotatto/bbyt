<template>
  <scroll-view class="circle-row" scroll-x :show-scrollbar="false" enhanced>
    <view class="circle-row__inner">
      <view
        v-for="(item, i) in items"
        :key="item.id ?? i"
        class="circle-row__item"
        @tap="$emit('select', i)"
      >
        <view class="circle-row__circle">
          <AppIcon :name="item.icon" :size="40" tone="primary" />
        </view>
        <text class="circle-row__label">{{ item.label }}</text>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import AppIcon from './AppIcon.vue'

/**
 * 圆形图标入口行，横向可滚（接后端 categories）。
 *
 * 用 enhanced + show-scrollbar=false：微信默认会在横滑区底部压一条
 * 滚动条，视觉上很脏。
 *
 * inner 用 inline-flex + 两端 padding：横滑内容的首尾要和页面边距对齐，
 * 但内容本身要能滑到边缘以外，所以 padding 加在内层而不是 scroll-view 上。
 */
defineProps<{
  items: { icon: string; label: string; id?: string }[]
}>()

defineEmits<{ select: [index: number] }>()
</script>

<style scoped>
.circle-row {
  width: 100%;
  white-space: nowrap;
}

.circle-row__inner {
  display: inline-flex;
  gap: var(--space-xl);
  padding: 0 var(--space-xs);
}

.circle-row__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 104rpx;
}

.circle-row__circle {
  width: 96rpx;
  height: 96rpx;
  border-radius: var(--radius-circle);
  background: var(--color-primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-row__label {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin-top: var(--space-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 104rpx;
}
</style>
