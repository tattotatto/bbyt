<template>
  <view class="benefit">
    <view class="benefit__main" @tap="$emit('mainTap')">
      <text class="benefit__main-title">{{ main.title }}</text>
      <text class="benefit__main-desc">{{ main.desc }}</text>
      <view v-if="main.action" class="benefit__main-pill">
        <text class="benefit__main-pill-text">{{ main.action }}</text>
      </view>
    </view>

    <view class="benefit__side">
      <view
        v-for="(item, i) in side"
        :key="i"
        class="benefit__side-card"
        @tap="$emit('sideTap', i)"
      >
        <AppIcon :name="item.icon" :size="36" tone="primary" />
        <text class="benefit__side-title">{{ item.title }}</text>
        <text v-if="item.desc" class="benefit__side-desc">{{ item.desc }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from './AppIcon.vue'

/**
 * 会员权益双栏卡：左侧一张大卡（品牌色渐变），右侧两张小卡。
 *
 * side 要求恰好 2 个 —— 三张会挤，一张会让右栏塌。用 CSS 让它自己
 * 撑成一列两行，不写死高度。
 */
defineProps<{
  main: { title: string; desc: string; action?: string }
  side: { icon: string; title: string; desc?: string }[]
}>()

defineEmits<{ mainTap: []; sideTap: [index: number] }>()
</script>

<style scoped>
.benefit {
  display: flex;
  gap: var(--space-md);
}

.benefit__main {
  flex: 1.35;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 200rpx;
}

.benefit__main-title {
  color: var(--text-white);
  font-size: var(--font-lg);
  font-weight: var(--font-weight-bold);
}

.benefit__main-desc {
  color: rgba(255, 255, 255, 0.9);
  font-size: var(--font-xs);
  margin-top: var(--space-xs);
  line-height: var(--leading-normal);
}

.benefit__main-pill {
  align-self: flex-start;
  background: var(--bg-white);
  border-radius: var(--radius-pill);
  padding: 6rpx 20rpx;
  margin-top: var(--space-sm);
}

.benefit__main-pill-text {
  font-size: var(--font-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}

.benefit__side {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.benefit__side-card {
  flex: 1;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.benefit__side-title {
  font-size: var(--font-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-top: var(--space-xs);
}

.benefit__side-desc {
  font-size: var(--font-xs);
  color: var(--text-muted);
  margin-top: var(--space-2xs);
}
</style>
