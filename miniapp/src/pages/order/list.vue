<template>
  <view class="order-list-page">
    <!-- 1. Status Tabs -->
    <scroll-view class="tab-bar" scroll-x :show-scrollbar="false" :enhanced="true">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        :class="['tab-item', { 'tab-item--active': activeTab === tab.value }]"
        @tap="switchTab(tab.value)"
      >
        <text class="tab-text">{{ tab.label }}</text>
        <view v-if="activeTab === tab.value" class="tab-indicator" />
      </view>
    </scroll-view>

    <!-- 2. Loading State -->
    <PageLoading v-if="loading" type="list" :count="4" />

    <!-- 3. Error State -->
    <view v-else-if="errorMsg" class="error-wrapper">
      <text class="error-icon">😵</text>
      <text class="error-text">{{ errorMsg }}</text>
      <view class="error-retry-btn" @tap="loadOrders(true)">
        <text class="error-retry-text">重试</text>
      </view>
    </view>

    <!-- 4. Empty State -->
    <view v-else-if="orders.length === 0" class="empty-wrapper">
      <EmptyState
        icon="📋"
        title="暂无订单"
        description="快去挑选心仪的商品吧"
        :showButton="true"
        buttonText="去逛逛"
        @buttonClick="goShopping"
      />
    </view>

    <!-- 5. Order Cards List -->
    <scroll-view
      v-else
      class="order-scroll"
      scroll-y
      :enhanced="true"
      :show-scrollbar="false"
      :refresher-enabled="false"
      @scrolltolower="onScrollToLower"
    >
      <view
        v-for="order in orders"
        :key="order.id"
        class="order-card"
      >
        <!-- Header -->
        <view class="order-header" @tap="goToDetail(order.id)">
          <text class="order-number">{{ order.order_no }}</text>
          <text
            class="order-status"
            :style="{ color: getStatusInfo(order.status).color, background: getStatusInfo(order.status).bg }"
          >{{ order.status_label || getStatusInfo(order.status).label }}</text>
        </view>

        <!-- Items -->
        <view
          v-for="item in order.items"
          :key="item.product_id"
          class="order-item"
          @tap="goToDetail(order.id)"
        >
          <image
            v-if="item.product_image"
            :src="item.product_image"
            class="item-img"
            mode="aspectFill"
          />
          <view v-else :class="['item-img-placeholder', getPlaceholderClass(item.product_id)]" />
          <view class="item-info">
            <text class="item-name">{{ item.product_name }}</text>
            <text class="item-spec">{{ item.spec }}</text>
            <view class="item-bottom-row">
              <text class="item-price">{{ formatPrice(item.unit_price) }}</text>
              <text class="item-qty">x{{ item.quantity }}</text>
            </view>
          </view>
        </view>

        <!-- Bottom Action Row -->
        <view class="order-bottom">
          <text class="order-total">合计：{{ formatPrice(order.final_amount) }}</text>
          <view class="order-actions">
            <!-- Status 0: 待付款 -->
            <template v-if="order.status === 0">
              <view class="btn-border" hover-class="btn-hover" @tap="handleCancelOrder(order)">
                <text class="btn-border-text">取消订单</text>
              </view>
              <view class="btn-solid" hover-class="btn-solid-hover" @tap="handlePayOrder(order)">
                <text class="btn-solid-text">立即付款</text>
              </view>
            </template>
            <!-- Status 1: 待发货 -->
            <template v-else-if="order.status === 1">
              <view class="btn-border" hover-class="btn-hover" @tap="handleRefundOrder(order)">
                <text class="btn-border-text">申请退款</text>
              </view>
              <view class="btn-solid" hover-class="btn-solid-hover" @tap="handleRemindShip(order)">
                <text class="btn-solid-text">提醒发货</text>
              </view>
            </template>
            <!-- Status 2: 已发货 -->
            <template v-else-if="order.status === 2">
              <view class="btn-border" hover-class="btn-hover" @tap="handleViewLogistics(order)">
                <text class="btn-border-text">查看物流</text>
              </view>
              <view class="btn-solid" hover-class="btn-solid-hover" @tap="handleConfirmReceive(order)">
                <text class="btn-solid-text">确认收货</text>
              </view>
            </template>
            <!-- Status 3: 已完成 -->
            <template v-else-if="order.status === 3">
              <view class="btn-solid" hover-class="btn-solid-hover" @tap="handleBuyAgain(order)">
                <text class="btn-solid-text">再次购买</text>
              </view>
            </template>
            <!-- Status 4/5: 已取消/退款中 -->
            <template v-else>
              <view class="btn-solid btn-solid--muted" hover-class="btn-solid-hover" @tap="handleBuyAgain(order)">
                <text class="btn-solid-text">再次购买</text>
              </view>
            </template>
          </view>
        </view>
      </view>

      <!-- Load More -->
      <view v-if="orders.length > 0" class="load-more">
        <text v-if="loadingMore" class="load-more-text">加载中...</text>
        <text v-else-if="!hasMore" class="load-more-text load-more-text--end">— 没有更多了 —</text>
      </view>

      <!-- Bottom Safe -->
      <view class="list-bottom-safe" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { getOrderList, cancelOrder, confirmReceipt } from '../../api/orders'
import type { Order } from '../../api/orders'
import { formatPrice, showSuccess, showError, showLoading, hideLoading } from '../../utils/index'
import { ORDER_STATUS, PAGE_SIZE } from '../../utils/constants'

// ── Tabs ──────────────────────────────────────
interface TabItem {
  label: string
  value: string
  statusCode: number | undefined
}

const tabs: TabItem[] = [
  { label: '全部', value: 'all', statusCode: undefined },
  { label: '待付款', value: 'pending_payment', statusCode: ORDER_STATUS.PENDING_PAYMENT.code },
  { label: '待发货', value: 'pending_shipping', statusCode: ORDER_STATUS.PENDING_SHIPPING.code },
  { label: '已发货', value: 'shipped', statusCode: ORDER_STATUS.SHIPPED.code },
  { label: '已完成', value: 'completed', statusCode: ORDER_STATUS.COMPLETED.code },
]

const activeTab = ref<string>('all')

// ── State ─────────────────────────────────────
const orders = ref<Order[]>([])
const loading = ref<boolean>(true)
const loadingMore = ref<boolean>(false)
const errorMsg = ref<string>('')
const page = ref<number>(1)
const hasMore = ref<boolean>(true)
const total = ref<number>(0)

// ── Status Helpers ────────────────────────────
function getStatusInfo(status: number): { label: string; color: string; bg: string } {
  const map: Record<number, { label: string; color: string; bg: string }> = {
    [ORDER_STATUS.PENDING_PAYMENT.code]: { label: ORDER_STATUS.PENDING_PAYMENT.label, color: '#FF7B7B', bg: '#FFF0F0' },
    [ORDER_STATUS.PENDING_SHIPPING.code]: { label: ORDER_STATUS.PENDING_SHIPPING.label, color: '#FF9F43', bg: '#FFF8F0' },
    [ORDER_STATUS.SHIPPED.code]: { label: ORDER_STATUS.SHIPPED.label, color: '#7EC8E3', bg: '#F0F8FB' },
    [ORDER_STATUS.COMPLETED.code]: { label: ORDER_STATUS.COMPLETED.label, color: '#A8D8B9', bg: '#F2FAF5' },
    [ORDER_STATUS.CANCELLED.code]: { label: ORDER_STATUS.CANCELLED.label, color: '#7a6a5a', bg: '#F5F5F5' },
    [ORDER_STATUS.REFUNDING.code]: { label: ORDER_STATUS.REFUNDING.label, color: '#FF7B7B', bg: '#FFF0F0' },
  }
  return map[status] || { label: '未知', color: '#7a6a5a', bg: '#F5F5F5' }
}

function getPlaceholderClass(id: number): string {
  const classes = ['img-ph--0', 'img-ph--1', 'img-ph--2', 'img-ph--3']
  return classes[id % classes.length]
}

// ── Data Loading ──────────────────────────────
async function loadOrders(reset: boolean = false) {
  if (reset) {
    page.value = 1
    hasMore.value = true
    orders.value = []
    loading.value = true
    errorMsg.value = ''
  }

  try {
    const currentTab = tabs.find(t => t.value === activeTab.value)
    const res = await getOrderList({
      page: page.value,
      page_size: PAGE_SIZE,
      status: currentTab?.statusCode,
    })
    const result = res.data

    if (reset) {
      orders.value = result.list
    } else {
      orders.value = [...orders.value, ...result.list]
    }

    total.value = result.total
    hasMore.value = orders.value.length < result.total
  } catch (err: any) {
    if (reset) {
      errorMsg.value = err.message || '加载失败，请稍后重试'
    } else {
      showError(err.message || '加载失败')
    }
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  page.value++
  await loadOrders(false)
}

// ── Tab Switch ────────────────────────────────
function switchTab(tabValue: string) {
  if (activeTab.value === tabValue) return
  activeTab.value = tabValue
  loadOrders(true)
}

// ── Lifecycle ─────────────────────────────────
onLoad((options?: AnyObject) => {
  const statusParam = options?.status
  if (statusParam !== undefined && statusParam !== null && statusParam !== '') {
    activeTab.value = String(statusParam)
  }
  loadOrders(true)
})

onPullDownRefresh(() => {
  page.value = 1
  hasMore.value = true
  loadOrders(true).finally(() => {
    uni.stopPullDownRefresh()
  })
})

function onScrollToLower() {
  loadMore()
}

// ── Navigation ────────────────────────────────
function goToDetail(orderId: number) {
  uni.navigateTo({ url: `/pages/order/detail?id=${orderId}` })
}

function goShopping() {
  uni.switchTab({ url: '/pages/products/index' })
}

// ── Actions ───────────────────────────────────
async function handleCancelOrder(order: Order) {
  const res = await new Promise<boolean>(resolve => {
    uni.showModal({
      title: '取消订单',
      content: '确定要取消该订单吗？',
      success: (modalRes) => resolve(modalRes.confirm),
    })
  })
  if (!res) return

  try {
    showLoading('取消中...')
    await cancelOrder(order.id)
    hideLoading()
    showSuccess('订单已取消')
    loadOrders(true)
  } catch (err: any) {
    hideLoading()
    showError(err.message || '取消失败')
  }
}

function handlePayOrder(order: Order) {
  showSuccess('模拟支付成功')
  setTimeout(() => {
    goToDetail(order.id)
  }, 1000)
}

async function handleConfirmReceive(order: Order) {
  const res = await new Promise<boolean>(resolve => {
    uni.showModal({
      title: '确认收货',
      content: '确认已收到商品？',
      success: (modalRes) => resolve(modalRes.confirm),
    })
  })
  if (!res) return

  try {
    showLoading('确认中...')
    await confirmReceipt(order.id)
    hideLoading()
    showSuccess('已确认收货')
    loadOrders(true)
  } catch (err: any) {
    hideLoading()
    showError(err.message || '确认失败')
  }
}

function handleViewLogistics(order: Order) {
  uni.showToast({ title: '物流信息查询中', icon: 'none' })
}

function handleBuyAgain(order: Order) {
  uni.showToast({ title: '已加入购物车', icon: 'success' })
}

function handleRemindShip(order: Order) {
  uni.showToast({ title: '已提醒卖家发货', icon: 'success' })
}

function handleRefundOrder(order: Order) {
  uni.showToast({ title: '退款申请已提交', icon: 'none' })
}
</script>

<style scoped>
.order-list-page {
  background: #FFF8F0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ===== Tab Bar ===== */
.tab-bar {
  display: flex;
  flex-direction: row;
  white-space: nowrap;
  background: #ffffff;
  padding: 0 8rpx;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.tab-item {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 28rpx;
}

.tab-text {
  font-size: 28rpx;
  color: #7a6a5a;
}

.tab-item--active .tab-text {
  color: #FF7B7B;
  font-weight: 600;
}

.tab-indicator {
  position: absolute;
  bottom: 4rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 4rpx;
  background: #FF7B7B;
  border-radius: 2px;
}

/* ===== Error State ===== */
.error-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 0;
}

.error-icon {
  font-size: 80rpx;
  line-height: 1.2;
}

.error-text {
  font-size: 28rpx;
  color: #7a6a5a;
  margin-top: 24rpx;
  text-align: center;
}

.error-retry-btn {
  margin-top: 32rpx;
  padding: 14rpx 48rpx;
  border-radius: 50px;
  border: 1px solid #FF7B7B;
}

.error-retry-text {
  font-size: 28rpx;
  color: #FF7B7B;
  font-weight: 500;
}

/* ===== Empty State ===== */
.empty-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ===== Order Scroll ===== */
.order-scroll {
  flex: 1;
}

/* ===== Order Card ===== */
.order-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24rpx;
  margin: 16rpx 24rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

/* Order Header */
.order-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16rpx;
  border-bottom: 1px solid #f5f5f5;
}

.order-number {
  font-size: 24rpx;
  color: #7a6a5a;
}

.order-status {
  font-size: 24rpx;
  font-weight: 500;
  padding: 4rpx 16rpx;
  border-radius: 50px;
}

/* Order Item */
.order-item {
  display: flex;
  flex-direction: row;
  padding: 20rpx 0;
  border-bottom: 1px solid #f5f5f5;
}

.order-item:last-of-type {
  border-bottom: none;
}

.item-img {
  width: 160rpx;
  height: 160rpx;
  border-radius: 12px;
  flex-shrink: 0;
}

.item-img-placeholder {
  width: 160rpx;
  height: 160rpx;
  border-radius: 12px;
  flex-shrink: 0;
}

.img-ph--0 { background: #FFE0E0; }
.img-ph--1 { background: #E0F0FF; }
.img-ph--2 { background: #E0F8E8; }
.img-ph--3 { background: #FFFDE0; }

.item-info {
  flex: 1;
  margin-left: 20rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.item-name {
  font-size: 28rpx;
  color: #4a3728;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-spec {
  font-size: 24rpx;
  color: #7a6a5a;
  margin-top: 8rpx;
}

.item-bottom-row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.item-price {
  font-size: 28rpx;
  font-weight: 600;
  color: #FF7B7B;
}

.item-qty {
  font-size: 24rpx;
  color: #7a6a5a;
}

/* Order Bottom */
.order-bottom {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding-top: 16rpx;
  border-top: 1px solid #f5f5f5;
  margin-top: 8rpx;
}

.order-total {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
}

.order-actions {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16rpx;
}

/* ===== Buttons ===== */
.btn-solid {
  border-radius: 50px;
  background: #FF7B7B;
  padding: 8px 24px;
}

.btn-solid--muted {
  background: #b0a090;
}

.btn-solid-hover {
  opacity: 0.85;
}

.btn-solid-text {
  font-size: 24rpx;
  color: #ffffff;
  font-weight: 500;
}

.btn-border {
  border-radius: 50px;
  border: 1px solid #f0e0d0;
  background: #ffffff;
  padding: 8px 24px;
}

.btn-hover {
  background: #f8f8f8;
}

.btn-border-text {
  font-size: 24rpx;
  color: #7a6a5a;
}

/* ===== Load More ===== */
.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
}

.load-more-text {
  font-size: 24rpx;
  color: #b0a090;
}

.load-more-text--end {
  color: #b0a090;
}

/* ===== Bottom Safe ===== */
.list-bottom-safe {
  height: calc(40rpx + env(safe-area-inset-bottom));
}
</style>
