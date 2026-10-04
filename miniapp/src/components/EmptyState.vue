<template>
  <view class="empty-state">
    <image
      v-if="image"
      :src="image"
      class="empty-state__image"
      mode="aspectFit"
    />
    <view v-else class="empty-state__icon">
      <AppIcon :name="illustrationName" :size="140" tone="muted" />
    </view>
    <text class="empty-state__title">{{ title }}</text>
    <text v-if="description" class="empty-state__desc">{{ description }}</text>
    <view
      v-if="showButton"
      class="empty-state__btn"
      @tap="handleClick"
    >
      <text class="empty-state__btn-text">{{ buttonText }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'
import { iconForEmoji } from '../utils/icon-map'

interface Props {
  /**
   * @deprecated 传进来的是 emoji，已不再直接渲染，而是查 `EMOJI_TO_ICON`
   * 换成图标字体。**25 个调用方全都还在传它**，所以保留原名与语义 ——
   * 删掉或改名会让那 25 处（含范围外的 10 个子页面）静默失去插画。
   * 新代码请用 `illustration`。等子页面铺开统一改完后，这个 prop 可以删。
   */
  icon?: string
  title?: string
  description?: string
  showButton?: boolean
  buttonText?: string
  image?: string
  /**
   * u-icon 空状态插画名，优先于 `icon`。图标集里有 13 个 `empty-*`：
   * empty-address / empty-car / empty-coupon / empty-data / empty-favor /
   * empty-history / empty-list / empty-news / empty-order / empty-page /
   * empty-permission / empty-search / empty-wifi
   *
   * 默认空串而不是 'empty-data'，这样「没传」与「传了」能区分开：
   * 没传才回落到 `icon` 的查表结果。两者都不给时结果仍是 'empty-data'。
   */
  illustration?: string
}

const props = withDefaults(defineProps<Props>(), {
  icon: '📦',
  title: '暂无数据',
  description: '',
  showButton: false,
  buttonText: '去逛逛',
  image: '',
  illustration: '',
})

const emit = defineEmits<{
  buttonClick: []
}>()

/**
 * 插画名。
 *
 * `illustration` 显式给了就用它 —— 那是新的写法。
 *
 * 否则把 `icon`（emoji）查表换成图标名。**这一步不能省**：25 个调用方
 * 全都传 emoji 的 `icon`（⚠️ 加载失败 / 🔐 请先登录 / 🛒 购物车为空 /
 * 💖 收藏为空 / 📍 无收货地址 …）。如果像计划里那样直接忽略 `icon`，
 * 这 25 处会全部变成同一张 'empty-data' 插画 —— 「加载失败」和
 * 「购物车为空」长得一模一样，那是功能退化，不是重构。
 *
 * 兜底用 'empty-data'（uview 的空数据插画），与计划给 illustration
 * 定的默认值一致。
 */
const illustrationName = computed(() => {
  if (props.illustration) return props.illustration
  return iconForEmoji(props.icon, 'empty-data')
})

function handleClick() {
  emit('buttonClick')
}
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 80rpx 0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

.empty-state__image {
  width: 200rpx;
  height: 200rpx;
}

/* 图标容器只负责居中；尺寸与颜色由 AppIcon 的 props 决定，
   所以这里不再写 font-size（旧版的 80rpx 是给 emoji 字形用的）。 */
.empty-state__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-lg);
  line-height: 1;
}

.empty-state__title {
  font-size: 30rpx;
  color: #4a3728;
  font-weight: 500;
  margin-top: 24rpx;
  text-align: center;
}

.empty-state__desc {
  font-size: 26rpx;
  color: #7a6a5a;
  margin-top: 12rpx;
  text-align: center;
  line-height: 1.5;
}

.empty-state__btn {
  margin-top: 32rpx;
  background: #e16531;
  border-radius: 50px;
  padding: 14px 48px;
}

.empty-state__btn-text {
  font-size: 28rpx;
  color: #fff;
  font-weight: 500;
}
</style>
