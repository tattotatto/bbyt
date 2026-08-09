<template>
  <view class="settings-page">
    <!-- Settings Menu -->
    <view class="menu-card">
      <view class="menu-item" @tap="handleClearCache">
        <text class="menu-icon">&#x1F5D1;</text>
        <text class="menu-title">清空缓存</text>
        <text class="menu-arrow">&#x203A;</text>
      </view>
      <view class="menu-item menu-item--last">
        <text class="menu-icon">&#x2139;</text>
        <text class="menu-title">关于</text>
        <text class="menu-value">HX Mall v1.0.0</text>
      </view>
    </view>

    <!-- Logout -->
    <view class="logout-section">
      <view class="btn-logout" @tap="handleLogout">
        <text class="btn-logout-text">退出登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useUserStore } from '../../../stores/user'
import { clearStorage, showSuccess } from '../../../utils/index'

const userStore = useUserStore()

function handleClearCache() {
  uni.showModal({
    title: '提示',
    content: '确定要清空所有缓存数据吗？',
    success: (res) => {
      if (res.confirm) {
        clearStorage()
        showSuccess('缓存已清空')
      }
    },
  })
}

function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
        showSuccess('已退出登录')
      }
    },
  })
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: #FFF8F0;
  padding: 24rpx;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* Menu Card */
.menu-card {
  background: #ffffff;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.menu-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 28rpx 32rpx;
  border-bottom: 1px solid #f5f5f5;
}

.menu-item--last {
  border-bottom: none;
}

.menu-icon {
  font-size: 34rpx;
  margin-right: 20rpx;
  flex-shrink: 0;
}

.menu-title {
  flex: 1;
  font-size: 28rpx;
  color: #4a3728;
}

.menu-arrow {
  font-size: 32rpx;
  color: #c4b5a5;
  flex-shrink: 0;
}

.menu-value {
  font-size: 26rpx;
  color: #7a6a5a;
  flex-shrink: 0;
}

/* Logout */
.logout-section {
  margin-top: 60rpx;
}

.btn-logout {
  width: 100%;
  height: 88rpx;
  border-radius: 50px;
  background: #ffffff;
  border: 1px solid #FF7B7B;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.btn-logout-text {
  font-size: 30rpx;
  font-weight: 500;
  color: #FF7B7B;
}
</style>
