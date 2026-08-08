<template>
  <view class="order-detail-page">
    <!-- 1. Loading State -->
    <PageLoading v-if="loading" type="detail" />

    <!-- 2. Error State -->
    <view v-else-if="errorMsg" class="error-wrapper">
      <text class="error-icon">😵</text>
      <text class="error-text">{{ errorMsg }}</text>
      <view class="error-retry-btn" @tap="loadOrderDetail">
        <text class="error-retry-text">重试</text>
      </view>
    </view>

    <!-- 3. Not Found -->
    <view v-else-if="!order" class="empty-wrapper">
      <EmptyState
        icon="📋"
        title="订单不存在"
        description="该订单可能已被删除"
        :showButton="true"
        buttonText="返回订单列表"
        @buttonClick="goBack"
      />
    </view>

    <!-- 4. Order Detail Content -->
    <template v-else>
      <!-- Status Header Banner -->
      <view class="status-header" :style="{ background: orderStatusBg(order.status) }">
        <text class="status-icon">{{ statusIcon }}</text>
        <text class="status-text" :style="{ color: orderStatusColor(order.status) }">
          {{ orderStatusLabel(order.status) }}
        </text>
        <text class="status-sub">{{ statusSubText }}</text>
      </view>

      <!-- Receiver Info Card -->
      <view v-if="order.receiver_name" class="address-card">
        <view class="address-row">
          <text class="address-icon">📍</text>
          <view class="address-info">
            <view class="address-contact">
              <text class="address-name">{{ order.receiver_name }}</text>
              <text class="address-phone">{{ order.receiver_phone ? maskPhone(order.receiver_phone) : '' }}</text>
            </view>
            <text class="address-detail">
              {{ order.receiver_address || '' }}
            </text>
          </view>
        </view>
      </view>

      <!-- Order Items Card -->
      <view class="items-card">
        <view
          v-for="(item, idx) in order.items"
          :key="item.product_id"
          class="item-row"
        >
          <image
            v-if="item.image"
            :src="item.image"
            class="item-img"
            mode="aspectFill"
          />
          <view v-else :class="['item-img-placeholder', getPlaceholderClass(item.product_id)]" />
          <view class="item-info">
            <text class="item-name">{{ item.name }}</text>
            <view class="item-price-row">
              <text class="item-price">{{ formatPrice(item.unit_price) }}</text>
              <text class="item-qty">x{{ item.qty }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- Price Breakdown Card -->
      <view class="price-card">
        <view class="price-row">
          <text class="price-label">商品总额</text>
          <text class="price-value">{{ formatCents(order.total_amount) }}</text>
        </view>
        <view class="price-row">
          <text class="price-label">运费</text>
          <text class="price-value">免运费</text>
        </view>
        <view class="price-row price-row--total">
          <text class="price-label price-label--total">实付款</text>
          <text class="price-value price-value--total">{{ formatCents(order.total_amount) }}</text>
        </view>
      </view>

      <!-- Order Info Card -->
      <view class="info-card">
        <view class="info-row">
          <text class="info-label">订单编号</text>
          <view class="info-value-row">
            <text class="info-value mono">{{ order.order_no }}</text>
            <text class="info-copy" @tap="copyOrderNo">复制</text>
          </view>
        </view>
        <view class="info-row">
          <text class="info-label">下单时间</text>
          <text class="info-value">{{ order.created_at ? formatDate(order.created_at) : '' }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">备注</text>
          <text class="info-value" :class="{ 'info-value--muted': !order.remark }">
            {{ order.remark || '无' }}
          </text>
        </view>
      </view>

      <!-- Timeline (if available) -->
      <view v-if="order.timeline && order.timeline.length > 0" class="timeline-card">
        <view class="timeline-title">订单跟踪</view>
        <view v-for="(entry, idx) in order.timeline" :key="idx" class="timeline-entry">
          <view class="timeline-dot" />
          <view v-if="idx < order.timeline.length - 1" class="timeline-line" />
          <view class="timeline-content">
            <text class="timeline-text">{{ entry.description || entry.event || '' }}</text>
            <text class="timeline-time">{{ entry.time ? formatDate(entry.time) : '' }}</text>
          </view>
        </view>
      </view>

      <!-- Bottom Spacer -->
      <view class="bottom-spacer" />

      <!-- Fixed Bottom Action Bar -->
      <view class="bottom-bar">
        <view class="bottom-actions">
          <!-- Status: pending_payment -->
          <template v-if="order.status === 'pending_payment'">
            <view class="btn-border" hover-class="btn-hover" @tap="handleCancelOrder">
              <text class="btn-border-text">取消订单</text>
            </view>
          </template>
          <!-- Status: paid -->
          <template v-else-if="order.status === 'paid'">
            <view class="btn-border" hover-class="btn-hover" @tap="handleRefundOrder">
              <text class="btn-border-text">申请退款</text>
            </view>
          </template>
          <!-- Status: shipped -->
          <template v-else-if="order.status === 'shipped'">
            <view class="btn-border" hover-class="btn-hover" @tap="handleRefundOrder">
              <text class="btn-border-text">申请退款</text>
            </view>
            <view class="btn-solid" hover-class="btn-solid-hover" @tap="handleConfirmReceive">
              <text class="btn-solid-text">确认收货</text>
            </view>
          </template>
          <!-- Status: confirmed / completed -->
          <template v-else-if="order.status === 'confirmed' || order.status === 'completed'">
            <view class="btn-solid" hover-class="btn-solid-hover" @tap="handleBuyAgain">
              <text class="btn-solid-text">再次购买</text>
            </view>
          </template>
          <!-- Status: cancelled / refunding / other -->
          <template v-else>
            <view class="btn-solid btn-solid--muted" hover-class="btn-solid-hover" @tap="handleBuyAgain">
              <text class="btn-solid-text">再次购买</text>
            </view>
          </template>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { getOrderDetail, cancelOrder, confirmReceipt, requestRefund } from '../../api/orders'
import type { Order } from '../../api/orders'
import { formatPrice, formatDate, maskPhone, showSuccess, showError, showLoading, hideLoading } from '../../utils/index'
import { orderStatusLabel, orderStatusColor, orderStatusBg, formatCents } from '../../utils/mapping'

// ── State ─────────────────────────────────────
const order = ref<Order | null>(null)
const loading = ref<boolean>(true)
const errorMsg = ref<string>('')

function getPlaceholderClass(id: string | number): string {
  const classes = ['img-ph--0', 'img-ph--1', 'img-ph--2', 'img-ph--3']
  const n = typeof id === 'string' ? id.length : id
  return classes[n % classes.length]
}

// ── Computed ──────────────────────────────────
const statusIcon = computed(() => {
  if (!order.value) return '📦'
  const icons: Record<string, string> = {
    pending_payment: '📦',
    paid: '📦',
    shipped: '🚚',
    confirmed: '✅',
    completed: '✅',
    cancelled: '❌',
    refunding: '❌',
  }
  return icons[order.value.status] || '📦'
})

const statusSubText = computed(() => {
  if (!order.value) return ''
  const texts: Record<string, string> = {
    pending_payment: '请尽快付款，订单将在30分钟后自动取消',
    paid: '已支付，等待卖家发货',
    shipped: '商品已发出，请注意查收',
    confirmed: '已确认收货，期待您的评价',
    completed: '交易已完成，期待您的再次光临',
    cancelled: '订单已取消',
    refunding: '退款处理中，请耐心等待',
  }
  return texts[order.value.status] || ''
})

// ── Data Loading ──────────────────────────────
async function loadOrderDetail() {
  loading.value = true
  errorMsg.value = ''

  try {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1] as any
    const orderId = currentPage?.options?.id
    if (!orderId) {
      errorMsg.value = '订单ID不存在'
      loading.value = false
      return
    }

    const res = await getOrderDetail(String(orderId))
    order.value = res.data
  } catch (err: any) {
    errorMsg.value = err.message || '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// ── Lifecycle ─────────────────────────────────
onLoad(() => {
  loadOrderDetail()
})

// ── Navigation ────────────────────────────────
function goBack() {
  uni.navigateBack()
}

// ── Clipboard ─────────────────────────────────
function copyOrderNo() {
  if (!order.value) return
  uni.setClipboardData({
    data: order.value.order_no,
    success: () => {
      showSuccess('已复制')
    },
  })
}

// ── Actions ───────────────────────────────────
async function handleCancelOrder() {
  if (!order.value) return

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
    await cancelOrder(order.value.id)
    hideLoading()
    showSuccess('订单已取消')
    loadOrderDetail()
  } catch (err: any) {
    hideLoading()
    showError(err.message || '取消失败')
  }
}

async function handleConfirmReceive() {
  if (!order.value) return

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
    await confirmReceipt(order.value.id)
    hideLoading()
    showSuccess('已确认收货')
    loadOrderDetail()
  } catch (err: any) {
    hideLoading()
    showError(err.message || '确认失败')
  }
}

async function handleRefundOrder() {
  if (!order.value) return

  const res = await new Promise<boolean>(resolve => {
    uni.showModal({
      title: '申请退款',
      content: '确定要申请退款吗？',
      success: (modalRes) => resolve(modalRes.confirm),
    })
  })
  if (!res) return

  try {
    showLoading('提交中...')
    await requestRefund(order.value.id)
    hideLoading()
    showSuccess('退款申请已提交')
    loadOrderDetail()
  } catch (err: any) {
    hideLoading()
    showError(err.message || '退款申请失败')
  }
}

function handleBuyAgain() {
  uni.showToast({ title: '已加入购物车', icon: 'success' })
}
</script>

<style scoped>
.order-detail-page {
  background: #FFF8F0;
  min-height: 100vh;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ===== Error State ===== */
.error-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
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
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

/* ===== Status Header Banner ===== */
.status-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48rpx 32rpx;
}

.status-icon {
  font-size: 72rpx;
  line-height: 1.2;
}

.status-text {
  font-size: 36rpx;
  font-weight: 600;
  margin-top: 12rpx;
}

.status-sub {
  font-size: 24rpx;
  color: #7a6a5a;
  margin-top: 8rpx;
  text-align: center;
  line-height: 1.5;
}

/* ===== Address Card ===== */
.address-card {
  background: #ffffff;
  border-radius: 16px;
  margin: 20rpx 24rpx;
  padding: 28rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.address-row {
  display: flex;
  flex-direction: row;
}

.address-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.address-info {
  flex: 1;
}

.address-contact {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 8rpx;
}

.address-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #4a3728;
  margin-right: 24rpx;
}

.address-phone {
  font-size: 26rpx;
  color: #7a6a5a;
}

.address-detail {
  font-size: 26rpx;
  color: #4a3728;
  line-height: 1.5;
}

/* ===== Items Card ===== */
.items-card {
  background: #ffffff;
  border-radius: 16px;
  margin: 0 24rpx 20rpx;
  padding: 0 24rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.item-row {
  display: flex;
  flex-direction: row;
  padding: 24rpx 0;
  border-bottom: 1px solid #f5f5f5;
}

.item-row:last-of-type {
  border-bottom: none;
}

.item-img {
  width: 120rpx;
  height: 120rpx;
  border-radius: 12px;
  flex-shrink: 0;
}

.item-img-placeholder {
  width: 120rpx;
  height: 120rpx;
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

.item-price-row {
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

/* ===== Price Summary Card ===== */
.price-card {
  background: #ffffff;
  border-radius: 16px;
  margin: 0 24rpx 20rpx;
  padding: 24rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.price-row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 10rpx 0;
}

.price-row--total {
  border-top: 1px solid #f0e0d0;
  padding-top: 16rpx;
  margin-top: 4rpx;
}

.price-label {
  font-size: 26rpx;
  color: #7a6a5a;
}

.price-value {
  font-size: 26rpx;
  color: #4a3728;
}

.price-value--discount {
  color: #A8D8B9;
}

.price-label--total {
  font-size: 28rpx;
  font-weight: 600;
  color: #4a3728;
}

.price-value--total {
  font-size: 32rpx;
  font-weight: 700;
  color: #FF7B7B;
}

/* ===== Order Info Card ===== */
.info-card {
  background: #ffffff;
  border-radius: 16px;
  margin: 0 24rpx 20rpx;
  padding: 24rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.info-row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 14rpx 0;
  border-bottom: 1px solid #f5f5f5;
}

.info-row:last-of-type {
  border-bottom: none;
}

.info-label {
  font-size: 26rpx;
  color: #7a6a5a;
  flex-shrink: 0;
  width: 140rpx;
}

.info-value {
  font-size: 26rpx;
  color: #4a3728;
  text-align: right;
  word-break: break-all;
}

.mono {
  font-family: "SF Mono", "Menlo", "Consolas", monospace;
  font-size: 24rpx;
}

.info-value--muted {
  color: #b0a090;
}

.info-value-row {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.info-copy {
  font-size: 22rpx;
  color: #FF7B7B;
  margin-left: 16rpx;
  padding: 4rpx 12rpx;
  border: 1px solid #FF7B7B;
  border-radius: 8px;
  flex-shrink: 0;
}

/* ===== Timeline Card ===== */
.timeline-card {
  background: #ffffff;
  border-radius: 16px;
  margin: 0 24rpx 20rpx;
  padding: 24rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.timeline-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #4a3728;
  margin-bottom: 16rpx;
}

.timeline-entry {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  padding: 8rpx 0;
  position: relative;
}

.timeline-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #FF7B7B;
  flex-shrink: 0;
  margin-top: 6rpx;
  z-index: 1;
}

.timeline-line {
  position: absolute;
  left: 7rpx;
  top: 28rpx;
  bottom: -8rpx;
  width: 2rpx;
  background: #f0e0d0;
}

.timeline-content {
  margin-left: 20rpx;
  flex: 1;
}

.timeline-text {
  font-size: 26rpx;
  color: #4a3728;
  line-height: 1.5;
}

.timeline-time {
  font-size: 22rpx;
  color: #b0a090;
  margin-top: 4rpx;
}

/* ===== Bottom ===== */
.bottom-spacer {
  height: 140rpx;
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #ffffff;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.04);
  z-index: 100;
}

.bottom-actions {
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
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
</style>
