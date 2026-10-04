<template>
  <view class="banner" :style="{ width: width }" @tap="$emit('tap')">
    <image v-if="image" class="banner__img" :src="image" mode="aspectFill" />
    <!-- 无图兜底：品牌色几何底纹。案例图目前还没有，这个兜底是常态而非例外。 -->
    <view v-else class="banner__img banner__img--placeholder">
      <AppIcon name="photo" :size="72" tone="white" />
    </view>

    <view class="banner__mask" />

    <view class="banner__content">
      <text class="banner__title">{{ title }}</text>
      <text v-if="subtitle" class="banner__subtitle">{{ subtitle }}</text>
      <view v-if="action" class="banner__pill">
        <text class="banner__pill-text">{{ action }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from './AppIcon.vue'

/**
 * 满宽横图卡：图 + 左深右浅的渐变遮罩 + 左下标题区 + 深棕胶囊按钮。
 *
 * 胶囊用 --color-ink(#2B2320) 而不是纯黑：素材里是纯黑配绿底，很跳；
 * 配珊瑚橙粉的暖调背景会发冷，换深棕。
 *
 * 遮罩从左上深到右浅（90deg），保证左下角文字在任何底图上都可读。
 */
withDefaults(defineProps<{
  title: string
  subtitle?: string
  image?: string
  action?: string
  width?: string
}>(), {
  subtitle: '',
  image: '',
  action: '查看详情',
  width: '100%',
})

defineEmits<{ tap: [] }>()
</script>

<style scoped>
.banner {
  position: relative;
  height: 260rpx;
  border-radius: var(--radius-hero);
  overflow: hidden;
  flex-shrink: 0;
}

.banner__img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.banner__img--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(115deg, var(--color-primary-light), var(--color-primary-mid));
  opacity: 0.9;
}

.banner__mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.05));
}

.banner__content {
  position: absolute;
  left: var(--space-lg);
  right: var(--space-lg);
  bottom: var(--space-lg);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.banner__title {
  color: var(--text-white);
  font-size: var(--font-lg);
  font-weight: var(--font-weight-bold);
  line-height: var(--leading-tight);
}

.banner__subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: var(--font-sm);
  margin-top: var(--space-2xs);
}

.banner__pill {
  background: var(--color-ink);
  border-radius: var(--radius-pill);
  padding: 8rpx 24rpx;
  margin-top: var(--space-sm);
}

.banner__pill-text {
  color: var(--text-white);
  font-size: var(--font-xs);
  font-weight: var(--font-weight-semibold);
}
</style>
