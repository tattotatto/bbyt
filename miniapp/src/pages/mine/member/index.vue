<template>
  <view class="member-page">
    <!-- ================================================================ -->
    <!--  STATE: LOADING -->
    <!-- ================================================================ -->
    <template v-if="pageState === 'loading'">
      <PageLoading type="full" />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: ERROR -->
    <!-- ================================================================ -->
    <template v-else-if="pageState === 'error'">
      <EmptyState
        icon="⚠️"
        title="加载失败"
        description="网络好像开小差了，请检查网络后重试"
        :showButton="true"
        buttonText="重新加载"
        @buttonClick="loadData"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: NOT LOGGED IN -->
    <!-- ================================================================ -->
    <template v-else-if="pageState === 'notLoggedIn'">
      <EmptyState
        icon="🔐"
        title="请先登录"
        description="登录后即可查看会员权益与账期额度"
        :showButton="true"
        buttonText="去登录"
        @buttonClick="goToMine"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: CONTENT — Member Center -->
    <!-- ================================================================ -->
    <template v-else-if="pageState === 'content'">
      <!-- ── Level Header Card ─────────────────────────────────────────── -->
      <view
        class="level-card"
        :style="{ background: levelHeaderBg }"
      >
        <view class="level-card-badge">
          <text class="level-card-icon">💎</text>
        </view>
        <text class="level-card-title">{{ userStore.levelLabel }}</text>
        <text class="level-card-subtitle">
          {{ levelDiscountLabel(profile?.level ?? 'normal') }}
        </text>
      </view>

      <!-- ── Discount / Benefits Card ──────────────────────────────────── -->
      <view class="info-card">
        <view class="info-card-header">
          <text class="info-card-icon">🏷️</text>
          <text class="info-card-title">会员权益</text>
        </view>
        <view class="info-card-divider" />
        <view class="info-card-body">
          <view class="benefit-row">
            <text class="benefit-label">等级折扣</text>
            <text class="benefit-value benefit-value--highlight">
              {{ levelDiscountLabel(profile?.level ?? 'normal') }}
            </text>
          </view>
          <view class="benefit-row">
            <text class="benefit-label">采购方式</text>
            <text class="benefit-value">按批发价采购</text>
          </view>
        </view>
      </view>

      <!-- ── Credit Card ───────────────────────────────────────────────── -->
      <view class="info-card">
        <view class="info-card-header">
          <text class="info-card-icon">💳</text>
          <text class="info-card-title">账期额度</text>
        </view>
        <view class="info-card-divider" />
        <view class="info-card-body">
          <view class="credit-grid">
            <view class="credit-item">
              <text class="credit-label">可用额度</text>
              <text class="credit-value credit-value--available">
                {{ formatCents(availableCredit) }}
              </text>
            </view>
            <view class="credit-item">
              <text class="credit-label">已用额度</text>
              <text class="credit-value credit-value--used">
                {{ formatCents(creditBalance) }}
              </text>
            </view>
            <view class="credit-item">
              <text class="credit-label">总额度</text>
              <text class="credit-value credit-value--total">
                {{ formatCents(creditLimit) }}
              </text>
            </view>
          </view>
        </view>
      </view>

      <!-- ── Company Info Card ─────────────────────────────────────────── -->
      <view v-if="profile?.retailer_profile" class="info-card">
        <view class="info-card-header">
          <text class="info-card-icon">🏢</text>
          <text class="info-card-title">企业信息</text>
        </view>
        <view class="info-card-divider" />
        <view class="info-card-body">
          <view class="info-row">
            <text class="info-label">公司名称</text>
            <text class="info-value">
              {{ profile.retailer_profile.company_name || '未填写' }}
            </text>
          </view>
          <view class="info-row info-row--last">
            <text class="info-label">联系人</text>
            <text class="info-value">
              {{ profile.retailer_profile.contact_person || '未填写' }}
            </text>
          </view>
        </view>
      </view>

      <!-- ── Purchase History Card ─────────────────────────────────────── -->
      <view
        v-if="profile?.retailer_profile?.purchase_history_summary"
        class="info-card"
      >
        <view class="info-card-header">
          <text class="info-card-icon">📊</text>
          <text class="info-card-title">购买画像</text>
        </view>
        <view class="info-card-divider" />
        <view class="info-card-body">
          <text class="history-text">
            {{ profile.retailer_profile.purchase_history_summary }}
          </text>
        </view>
      </view>

      <!-- ── Safe Area Bottom ──────────────────────────────────────────── -->
      <view class="member-safe-bottom" :style="{ height: safeBottom + 'px' }" />
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import PageLoading from '../../../components/PageLoading.vue'
import EmptyState from '../../../components/EmptyState.vue'
import { useUserStore } from '../../../stores/user'
import { getUserProfile } from '../../../api/auth'
import type { UserProfile } from '../../../api/auth'
import { formatCents, levelDiscountLabel, levelColor } from '../../../utils/mapping'

const userStore = useUserStore()

// ── Page State ──────────────────────────────────────────────────────────────
type PageState = 'loading' | 'error' | 'notLoggedIn' | 'content'
const pageState = ref<PageState>('loading')

// ── Profile Data ────────────────────────────────────────────────────────────
const profile = ref<UserProfile | null>(null)

// ── Computed ────────────────────────────────────────────────────────────────
const creditLimit = computed(() => profile.value?.credit_limit ?? 0)
const creditBalance = computed(() => profile.value?.credit_balance ?? 0)
const availableCredit = computed(() =>
  Math.max(0, creditLimit.value - creditBalance.value)
)

const levelHeaderBg = computed(() => {
  const color = levelColor(profile.value?.level ?? 'normal')
  return `linear-gradient(135deg, ${color}, ${color}CC)`
})

const safeBottom = computed(() => {
  try {
    const info = uni.getSystemInfoSync()
    const bottom = info.safeAreaInsets?.bottom || info.safeArea?.bottom || 0
    return Math.max(bottom, 20)
  } catch {
    return 20
  }
})

// ── Data Loading ───────────────────────────────────────────────────────────
async function loadData(): Promise<void> {
  if (!userStore.isLoggedIn) {
    pageState.value = 'notLoggedIn'
    return
  }
  pageState.value = 'loading'
  try {
    const res = await getUserProfile()
    profile.value = res.data
    pageState.value = 'content'
  } catch {
    pageState.value = 'error'
  }
}

// ── Navigation ─────────────────────────────────────────────────────────────
/**
 * Navigate to the "Mine" tab, which serves as the project's login entry point.
 * The mine page header presents the login UI when the user is not authenticated.
 */
function goToMine(): void {
  uni.switchTab({ url: '/pages/mine/index' })
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onShow(() => {
  loadData()
})
</script>

<style scoped>
.member-page {
  min-height: 100vh;
  background: #FFF8F0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ========================================================================== */
/*  LEVEL HEADER CARD                                                          */
/* ========================================================================== */
.level-card {
  margin: 24rpx 24rpx 20rpx;
  padding: 48rpx 32rpx;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.level-card-badge {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16rpx;
}

.level-card-icon {
  font-size: 52rpx;
  line-height: 1;
}

.level-card-title {
  font-size: 38rpx;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8rpx;
}

.level-card-subtitle {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.2);
  padding: 6rpx 24rpx;
  border-radius: 50px;
}

/* ========================================================================== */
/*  INFO CARDS                                                                 */
/* ========================================================================== */
.info-card {
  background: #ffffff;
  border-radius: 20px;
  margin: 0 24rpx 20rpx;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.info-card-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 28rpx 32rpx 20rpx;
}

.info-card-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
}

.info-card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #4a3728;
}

.info-card-divider {
  height: 1px;
  background: #f5f0eb;
  margin: 0 32rpx;
}

.info-card-body {
  padding: 24rpx 32rpx 28rpx;
}

/* ── Benefit Row ─────────────────────────────────── */
.benefit-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 0;
}

.benefit-label {
  font-size: 28rpx;
  color: #7a6a5a;
}

.benefit-value {
  font-size: 28rpx;
  color: #4a3728;
}

.benefit-value--highlight {
  color: #FF7B7B;
  font-weight: 600;
}

/* ── Credit Grid ─────────────────────────────────── */
.credit-grid {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}

.credit-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.credit-label {
  font-size: 24rpx;
  color: #7a6a5a;
  margin-bottom: 8rpx;
}

.credit-value {
  font-size: 32rpx;
  font-weight: 700;
  color: #4a3728;
}

.credit-value--available {
  color: #52C41A;
}

.credit-value--used {
  color: #FF7B7B;
}

.credit-value--total {
  color: #4a3728;
}

/* ── Info Row ────────────────────────────────────── */
.info-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 0;
}

.info-row--last {
  padding-bottom: 0;
}

.info-label {
  font-size: 28rpx;
  color: #7a6a5a;
  flex-shrink: 0;
}

.info-value {
  font-size: 28rpx;
  color: #4a3728;
  text-align: right;
  margin-left: 24rpx;
}

/* ── Purchase History Text ───────────────────────── */
.history-text {
  font-size: 28rpx;
  color: #4a3728;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-all;
}

/* ========================================================================== */
/*  SAFE AREA BOTTOM                                                           */
/* ========================================================================== */
.member-safe-bottom {
  width: 100%;
}
</style>
