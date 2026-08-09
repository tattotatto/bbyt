<template>
  <view class="contact-page">
    <!-- Service Info Card -->
    <view class="info-card">
      <view class="info-row">
        <text class="info-label">客服电话</text>
        <text class="info-value">400-000-0000</text>
      </view>
      <view class="info-row">
        <text class="info-label">客服微信</text>
        <text class="info-value">HXMall_KF (暂未开通)</text>
      </view>
      <view class="info-row info-row--last">
        <text class="info-label">服务时间</text>
        <text class="info-value">周一至周日 9:00 - 18:00</text>
      </view>
    </view>

    <!-- Call Button -->
    <view class="action-section">
      <view class="btn-call" @tap="handleCall">
        <text class="btn-call-icon">&#x260E;</text>
        <text class="btn-call-text">拨打电话</text>
      </view>
    </view>

    <!-- Tips -->
    <view class="tips-section">
      <text class="tips-text">如有任何问题，欢迎通过上述方式联系我们</text>
    </view>
  </view>
</template>

<script setup lang="ts">
const PHONE_NUMBER = '400-000-0000'

function handleCall() {
  uni.makePhoneCall({ phoneNumber: PHONE_NUMBER })
}
</script>

<style scoped>
.contact-page {
  min-height: 100vh;
  background: #FFF8F0;
  padding: 24rpx;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* Info Card */
.info-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 0 32rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.info-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 0;
  border-bottom: 1px solid #f5f5f5;
}

.info-row--last {
  border-bottom: none;
}

.info-label {
  font-size: 28rpx;
  color: #4a3728;
  font-weight: 500;
}

.info-value {
  font-size: 26rpx;
  color: #7a6a5a;
}

/* Action */
.action-section {
  margin-top: 40rpx;
}

.btn-call {
  width: 100%;
  height: 88rpx;
  border-radius: 50px;
  background: linear-gradient(135deg, #FF7B7B 0%, #FF9B9B 100%);
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(255, 123, 123, 0.3);
}

.btn-call-icon {
  font-size: 34rpx;
  color: #ffffff;
  margin-right: 12rpx;
}

.btn-call-text {
  font-size: 30rpx;
  font-weight: 500;
  color: #ffffff;
}

/* Tips */
.tips-section {
  margin-top: 32rpx;
  display: flex;
  justify-content: center;
}

.tips-text {
  font-size: 24rpx;
  color: #c4b5a5;
}
</style>
