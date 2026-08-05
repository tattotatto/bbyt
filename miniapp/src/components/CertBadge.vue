<template>
  <view class="cert-badge">
    <view class="cert-badge__dot"></view>
    <text class="cert-badge__name">{{ name }}</text>
  </view>
</template>

<script setup lang="ts">
interface Props {
  name: string
  icon?: string
}

withDefaults(defineProps<Props>(), {
  icon: 'shield',
})
</script>

<style scoped>
.cert-badge {
  display: inline-flex;
  align-items: center;
  background: #E8F8F0;
  border: 1px solid #C5E8D3;
  border-radius: 8px;
  font-size: 20rpx;
  padding: 2px 8px;
  color: #5A9E7C;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

.cert-badge__dot {
  width: 6rpx;
  height: 6rpx;
  border-radius: 50%;
  background: #A8D8B9;
  margin-right: 6rpx;
  flex-shrink: 0;
}

.cert-badge__name {
  white-space: nowrap;
  line-height: 1.4;
}
</style>
