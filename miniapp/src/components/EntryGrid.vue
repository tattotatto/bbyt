<template>
  <view class="entry-grid">
    <view
      v-for="(item, i) in items"
      :key="i"
      class="entry-grid__item"
      @tap="$emit('select', i)"
    >
      <view class="entry-grid__icon">
        <AppIcon :name="item.icon" :size="44" tone="primary" />
      </view>
      <text class="entry-grid__title">{{ item.title }}</text>
      <text v-if="item.subtitle" class="entry-grid__subtitle">{{ item.subtitle }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from './AppIcon.vue'

/** 快捷服务入口，3 列。图标居中、主标题加粗、副标题弱化。 */
defineProps<{
  items: { icon: string; title: string; subtitle?: string }[]
}>()

defineEmits<{ select: [index: number] }>()
</script>

<style scoped>
.entry-grid {
  display: flex;
  justify-content: space-around;
}

.entry-grid__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.entry-grid__icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: var(--radius-circle);
  background: var(--color-primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.entry-grid__title {
  font-size: var(--font-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-top: var(--space-sm);
}

.entry-grid__subtitle {
  font-size: var(--font-xs);
  color: var(--text-muted);
  margin-top: var(--space-2xs);
}
</style>
