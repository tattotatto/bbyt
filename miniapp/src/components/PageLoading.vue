<template>
  <view class="page-loading">
    <!-- Card skeletons -->
    <template v-if="type === 'card'">
      <view
        v-for="i in count"
        :key="i"
        class="page-loading__card"
      >
        <view class="page-loading__card-img skeleton"></view>
        <view class="page-loading__card-body">
          <view class="skeleton skeleton--text skeleton--long"></view>
          <view class="skeleton skeleton--text skeleton--medium"></view>
          <view class="skeleton skeleton--text skeleton--short"></view>
        </view>
      </view>
    </template>

    <!-- List skeletons -->
    <template v-else-if="type === 'list'">
      <view
        v-for="i in count"
        :key="i"
        class="page-loading__row"
      >
        <view class="page-loading__row-avatar skeleton"></view>
        <view class="page-loading__row-body">
          <view class="skeleton skeleton--text skeleton--long"></view>
          <view class="skeleton skeleton--text skeleton--short"></view>
        </view>
      </view>
    </template>

    <!-- Detail skeleton -->
    <template v-else-if="type === 'detail'">
      <view class="page-loading__detail">
        <view class="page-loading__detail-img skeleton"></view>
        <view class="skeleton skeleton--text skeleton--full"></view>
        <view class="skeleton skeleton--text skeleton--full"></view>
        <view class="skeleton skeleton--text skeleton--long"></view>
        <view class="skeleton skeleton--text skeleton--medium"></view>
        <view class="skeleton skeleton--text skeleton--short"></view>
      </view>
    </template>

    <!-- Full / spinner -->
    <template v-else>
      <view class="page-loading__full">
        <view class="page-loading__spinner"></view>
        <text class="page-loading__text">加载中...</text>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
interface Props {
  type?: 'card' | 'list' | 'detail' | 'full'
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  type: 'card',
  count: 3,
})
</script>

<style scoped>
.page-loading {
  background: #FFF8F0;
  padding: 24rpx;
  min-height: 100vh;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* Skeleton base */
.skeleton {
  background: linear-gradient(90deg, #f0e0d0 25%, #f5ebe0 50%, #f0e0d0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}

.skeleton--text {
  height: 24rpx;
  margin-bottom: 16rpx;
}

.skeleton--full {
  width: 100%;
}

.skeleton--long {
  width: 80%;
}

.skeleton--medium {
  width: 60%;
}

.skeleton--short {
  width: 40%;
}

/* Card skeleton */
.page-loading__card {
  background: #fff;
  border-radius: 20px;
  height: 280rpx;
  margin-bottom: 24rpx;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.page-loading__card-img {
  width: 100%;
  height: 180rpx;
  border-radius: 0;
}

.page-loading__card-body {
  padding: 16rpx 20rpx;
}

/* List skeleton */
.page-loading__row {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 12px;
  height: 100rpx;
  padding: 0 20rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.page-loading__row-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  flex-shrink: 0;
  margin-right: 16rpx;
}

.page-loading__row-body {
  flex: 1;
}

.page-loading__row-body .skeleton--text {
  margin-bottom: 12rpx;
}

/* Detail skeleton */
.page-loading__detail {
  padding: 0;
}

.page-loading__detail-img {
  width: 100%;
  height: 400rpx;
  border-radius: 20px;
  margin-bottom: 32rpx;
}

/* Full / spinner */
.page-loading__full {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 200rpx;
}

.page-loading__spinner {
  width: 64rpx;
  height: 64rpx;
  border: 4rpx solid #f0e0d0;
  border-top-color: #FF7B7B;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.page-loading__text {
  margin-top: 24rpx;
  font-size: 28rpx;
  color: #7a6a5a;
}

/* Animations */
@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
