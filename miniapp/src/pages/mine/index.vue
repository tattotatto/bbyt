<template>
  <view class="mine-page">
    <!-- ================================================================ -->
    <!--  1. Header — Coral Pink Gradient                                 -->
    <!-- ================================================================ -->
    <view class="profile-header">
      <!-- Logged in -->
      <template v-if="userStore.isLoggedIn">
        <view class="profile-avatar-wrapper">
          <image
            class="profile-avatar"
            :src="userStore.avatar"
            mode="aspectFill"
          />
        </view>
        <text class="profile-nickname">{{ userStore.nickname }}</text>
        <view class="profile-level-badge">
          <text class="profile-level-text">{{ userStore.levelLabel }}</text>
        </view>
        <text
          v-if="userStore.userInfo?.company_name"
          class="profile-company"
        >
          {{ userStore.userInfo.company_name }}
        </text>
      </template>

      <!-- Not logged in -->
      <template v-else>
        <view class="profile-avatar-wrapper profile-avatar--default" @tap="handleLogin">
          <text class="profile-avatar-emoji">👤</text>
        </view>
        <view class="profile-login-row" @tap="handleLogin">
          <text class="profile-login-text">点击登录</text>
          <text class="profile-login-arrow">›</text>
        </view>
      </template>
    </view>

    <!-- ================================================================ -->
    <!--  2. Order Overview Card (overlaps header via negative margin)     -->
    <!-- ================================================================ -->
    <view class="order-card">
      <view class="order-card-header">
        <text class="order-card-title">我的订单</text>
        <text class="order-card-all" @tap="goToOrders('all')">查看全部 ›</text>
      </view>
      <view class="order-shortcuts">
        <view class="order-shortcut" @tap="goToOrders('pending')">
          <text class="order-shortcut-icon">📋</text>
          <text class="order-shortcut-label">待付款</text>
        </view>
        <view class="order-shortcut" @tap="goToOrders('paid')">
          <text class="order-shortcut-icon">📦</text>
          <text class="order-shortcut-label">待发货</text>
        </view>
        <view class="order-shortcut" @tap="goToOrders('shipped')">
          <text class="order-shortcut-icon">🚚</text>
          <text class="order-shortcut-label">已发货</text>
        </view>
        <view class="order-shortcut" @tap="goToOrders('completed')">
          <text class="order-shortcut-icon">⭐</text>
          <text class="order-shortcut-label">已完成</text>
        </view>
        <view class="order-shortcut" @tap="goToRefund">
          <text class="order-shortcut-icon">🔄</text>
          <text class="order-shortcut-label">退款/售后</text>
        </view>
      </view>
    </view>

    <!-- ================================================================ -->
    <!--  3. Menu Section 1                                               -->
    <!-- ================================================================ -->
    <view class="menu-card">
      <view class="menu-item" @tap="navigateTo('/pages/mine/company')">
        <text class="menu-icon">🏢</text>
        <text class="menu-title">企业信息</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @tap="navigateTo('/pages/mine/address')">
        <text class="menu-icon">📍</text>
        <text class="menu-title">收货地址</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @tap="navigateTo('/pages/mine/member')">
        <text class="menu-icon">💎</text>
        <text class="menu-title">会员中心</text>
        <view class="menu-right">
          <text class="menu-level-tag">
            {{ userStore.isLoggedIn ? userStore.levelLabel : '普通会员' }}
          </text>
          <text class="menu-arrow">›</text>
        </view>
      </view>
      <view class="menu-item" @tap="navigateTo('/pages/mine/favorites')">
        <text class="menu-icon">🛒</text>
        <text class="menu-title">我的收藏</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @tap="navigateTo('/pages/mine/history')">
        <text class="menu-icon">👣</text>
        <text class="menu-title">浏览记录</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item menu-item--last" @tap="navigateTo('/pages/mine/coupons')">
        <text class="menu-icon">🎫</text>
        <text class="menu-title">优惠券</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- ================================================================ -->
    <!--  4. Menu Section 2                                               -->
    <!-- ================================================================ -->
    <view class="menu-card">
      <view class="menu-item" @tap="navigateTo('/pages/mine/contact')">
        <text class="menu-icon">📞</text>
        <text class="menu-title">联系客服</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @tap="navigateTo('/pages/mine/settings')">
        <text class="menu-icon">⚙️</text>
        <text class="menu-title">设置</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item menu-item--last" @tap="navigateTo('/pages/mine/help')">
        <text class="menu-icon">❓</text>
        <text class="menu-title">帮助中心</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- ================================================================ -->
    <!--  5. Logout Button (logged-in only)                               -->
    <!-- ================================================================ -->
    <view v-if="userStore.isLoggedIn" class="logout-section">
      <view class="btn-logout" @tap="handleLogout">
        <text class="btn-logout-text">退出登录</text>
      </view>
    </view>

    <!-- ================================================================ -->
    <!--  6. Version                                                      -->
    <!-- ================================================================ -->
    <view class="version-section">
      <text class="version-text">HX Mall v1.0.0</text>
    </view>

    <!-- ================================================================ -->
    <!--  7. Safe Area Bottom                                             -->
    <!-- ================================================================ -->
    <view class="mine-safe-bottom" :style="{ height: safeBottom + 'px' }" />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '../../stores/user'
import { useAppStore } from '../../stores/app'

const userStore = useUserStore()
const appStore = useAppStore()

// Init app store to get system info
appStore.init()

const safeBottom = computed(() => Math.max(appStore.safeAreaBottom, 20))

// ── Login ───────────────────────────────────────────────────────────────────
function handleLogin() {
  // Real implementation would use uni.login + wx.getUserProfile
  // For now, use mock login flow
  uni.showModal({
    title: '登录',
    content: '使用模拟账号登录？',
    success: (res) => {
      if (res.confirm) {
        userStore.login({
          code: 'mock_code_' + Date.now(),
          userInfo: {
            nickName: '小暖用户',
            avatarUrl: ''
          }
        })
        uni.showToast({ title: '登录成功', icon: 'success' })
      }
    }
  })
}

// ── Logout ──────────────────────────────────────────────────────────────────
function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
      }
    }
  })
}

// ── Navigation ──────────────────────────────────────────────────────────────
function goToOrders(status: string) {
  uni.navigateTo({ url: `/pages/order/list?status=${status}` })
}

function goToRefund() {
  uni.navigateTo({ url: '/pages/order/list?status=refunding' })
}

function navigateTo(url: string) {
  uni.navigateTo({ url })
}
</script>

<style scoped>
.mine-page {
  background: #FFF8F0;
  min-height: 100vh;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ========================================================================== */
/*  1. HEADER — Coral Pink Gradient                                           */
/* ========================================================================== */
.profile-header {
  background: linear-gradient(180deg, #FF7B7B 0%, #FF9B9B 100%);
  padding: 40rpx 32rpx 60rpx;
  border-radius: 0 0 40rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.profile-avatar-wrapper {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.5);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-avatar {
  width: 100%;
  height: 100%;
}

.profile-avatar--default {
  background: rgba(255, 255, 255, 0.4);
}

.profile-avatar-emoji {
  font-size: 60rpx;
  line-height: 1;
}

.profile-nickname {
  font-size: 36rpx;
  font-weight: 600;
  color: #ffffff;
  margin-top: 16rpx;
}

.profile-level-badge {
  margin-top: 8rpx;
  padding: 4rpx 20rpx;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 50px;
}

.profile-level-text {
  font-size: 22rpx;
  color: #ffffff;
}

.profile-company {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 8rpx;
}

.profile-login-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-top: 16rpx;
}

.profile-login-text {
  font-size: 32rpx;
  color: #ffffff;
  font-weight: 500;
}

.profile-login-arrow {
  font-size: 36rpx;
  color: rgba(255, 255, 255, 0.7);
  margin-left: 8rpx;
}

/* ========================================================================== */
/*  2. ORDER OVERVIEW CARD                                                    */
/* ========================================================================== */
.order-card {
  background: #ffffff;
  border-radius: 20px;
  margin: -30rpx 24rpx 20rpx;
  padding: 32rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.order-card-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32rpx;
}

.order-card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #4a3728;
}

.order-card-all {
  font-size: 26rpx;
  color: #7a6a5a;
}

.order-shortcuts {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}

.order-shortcut {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.order-shortcut-icon {
  font-size: 44rpx;
  line-height: 1.2;
}

.order-shortcut-label {
  font-size: 22rpx;
  color: #4a3728;
  margin-top: 8rpx;
}

/* ========================================================================== */
/*  3 & 4. MENU CARDS                                                         */
/* ========================================================================== */
.menu-card {
  background: #ffffff;
  border-radius: 20px;
  margin: 0 24rpx 20rpx;
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
  font-size: 36rpx;
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

.menu-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-shrink: 0;
}

.menu-level-tag {
  font-size: 22rpx;
  color: #FF7B7B;
  background: #FFF0F0;
  padding: 4rpx 12rpx;
  border-radius: 8px;
  margin-right: 12rpx;
}

/* ========================================================================== */
/*  5. LOGOUT BUTTON                                                          */
/* ========================================================================== */
.logout-section {
  margin: 40rpx 24rpx;
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

/* ========================================================================== */
/*  6. VERSION                                                                */
/* ========================================================================== */
.version-section {
  display: flex;
  justify-content: center;
  margin: 20rpx 0 40rpx;
}

.version-text {
  font-size: 22rpx;
  color: #c4b5a5;
}

/* ========================================================================== */
/*  7. SAFE AREA BOTTOM                                                       */
/* ========================================================================== */
.mine-safe-bottom {
  width: 100%;
}
</style>
