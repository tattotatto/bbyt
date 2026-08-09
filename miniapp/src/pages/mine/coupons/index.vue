<template>
  <view class="coupons-page">
    <EmptyState
      icon="🎫"
      title="优惠券"
      description="优惠券功能即将上线，敬请期待"
      :show-button="true"
      button-text="查看规则"
      @button-click="handleViewRules"
    />
  </view>
</template>

<script setup lang="ts">
// TODO: 第三方优惠券平台接入

function handleViewRules() {
  uni.showToast({ title: '敬请期待', icon: 'none' })
}
</script>

<style scoped>
.coupons-page {
  min-height: 100vh;
  background-color: #FFF8F0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
