<template>
  <view class="empty-state">
    <image
      v-if="image"
      :src="image"
      class="empty-state__image"
      mode="aspectFit"
    />
    <text v-else class="empty-state__icon">{{ icon }}</text>
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
interface Props {
  icon?: string
  title?: string
  description?: string
  showButton?: boolean
  buttonText?: string
  image?: string
}

withDefaults(defineProps<Props>(), {
  icon: '📦',
  title: '暂无数据',
  description: '',
  showButton: false,
  buttonText: '去逛逛',
  image: '',
})

const emit = defineEmits<{
  buttonClick: []
}>()

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

.empty-state__icon {
  font-size: 80rpx;
  line-height: 1.2;
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
  background: #FF7B7B;
  border-radius: 50px;
  padding: 14px 48px;
}

.empty-state__btn-text {
  font-size: 28rpx;
  color: #fff;
  font-weight: 500;
}
</style>
