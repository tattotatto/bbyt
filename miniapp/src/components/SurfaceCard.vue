<template>
  <view class="surface-card" :class="{ 'surface-card--overlap': overlap }" :style="cardStyle">
    <slot />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 悬浮白色圆角卡片。
 *
 * overlap=true 时用负 margin 上叠到品牌色头图区上 —— 这是整套布局语言里
 * 最关键的一笔（素材里白色内容卡片压在绿色头图下沿）。用负 margin 而不是
 * 绝对定位：卡片高度随内容变化，绝对定位会把它锁死。
 *
 * padding / radius 走 inline style 而不是 scoped class：调用方要能直接覆盖
 * （我的页的菜单卡要 padding: 0 才能让分隔线通到卡片边缘）。
 */
const props = withDefaults(defineProps<{
  overlap?: boolean
  padding?: string
  radius?: string
}>(), {
  overlap: false,
  padding: '32rpx',
  radius: 'var(--radius-lg)',
})

const cardStyle = computed(() => ({
  padding: props.padding,
  borderRadius: props.radius,
}))
</script>

<style scoped>
.surface-card {
  background: var(--bg-white);
  box-shadow: var(--shadow-card);
  position: relative;
}

.surface-card--overlap {
  margin-top: -48rpx;
  margin-left: var(--space-lg);
  margin-right: var(--space-lg);
}
</style>
