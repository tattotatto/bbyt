<template>
  <view class="checkout-page">
    <!-- Empty State -->
    <EmptyState
      v-if="!loading && checkoutItems.length === 0"
      icon="🛒"
      title="没有待结算商品"
      description="请先选择商品"
      :showButton="true"
      buttonText="去逛逛"
      @buttonClick="goShopping"
    />

    <template v-else>
      <!-- 1. Address Card -->
      <view class="address-card" @tap="selectAddress">
        <view v-if="selectedAddress" class="address-content">
          <text class="addr-icon">📍</text>
          <view class="addr-info">
            <view class="addr-contact">
              <text class="addr-name">{{ selectedAddress.name }}</text>
              <text class="addr-phone">{{ maskPhone(selectedAddress.phone) }}</text>
            </view>
            <text class="addr-full">
              {{ selectedAddress.province }}{{ selectedAddress.city }}{{ selectedAddress.district }} {{ selectedAddress.detail }}
            </text>
          </view>
          <text class="addr-arrow">›</text>
        </view>
        <view v-else class="address-empty">
          <text class="addr-empty-text">+ 添加收货地址</text>
        </view>
      </view>

      <!-- 2. Order Items -->
      <view class="items-card">
        <view class="items-header">
          <text class="items-header-text">商品信息</text>
          <text class="items-count">共 {{ checkoutItems.length }} 件</text>
        </view>
        <view
          v-for="(item, idx) in checkoutItems"
          :key="item.productId + '_' + item.spec"
          class="item-row"
        >
          <image
            v-if="item.productImage"
            :src="item.productImage"
            class="item-img"
            mode="aspectFill"
          />
          <view v-else :class="['item-img-placeholder', 'img-ph--' + (idx % 4)]" />
          <view class="item-info">
            <text class="item-name">{{ item.productName }}</text>
            <text class="item-spec">{{ item.spec }}</text>
            <view class="item-price-row">
              <text class="item-price">{{ formatPrice(item.unitPrice) }}</text>
              <text class="item-qty">×{{ item.quantity }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 3. Remark -->
      <view class="remark-card">
        <text class="remark-label">订单备注</text>
        <textarea
          v-model="remark"
          placeholder="选填：如有特殊需求请备注"
          :maxlength="200"
          class="remark-input"
        />
        <text class="remark-count">{{ remark.length }}/200</text>
      </view>

      <!-- 4. Payment Method -->
      <view class="payment-card">
        <text class="section-title">支付方式</text>
        <view
          class="payment-option"
          :class="{ active: paymentMethod === 'wechat' }"
          @tap="paymentMethod = 'wechat'"
        >
          <view class="radio" :class="{ checked: paymentMethod === 'wechat' }" />
          <text class="method-icon">💚</text>
          <text class="method-label">微信支付</text>
        </view>
        <view
          class="payment-option"
          :class="{ active: paymentMethod === 'balance' }"
          @tap="paymentMethod = 'balance'"
        >
          <view class="radio" :class="{ checked: paymentMethod === 'balance' }" />
          <text class="method-icon">💰</text>
          <text class="method-label">余额支付</text>
        </view>
      </view>

      <!-- 5. Price Breakdown -->
      <view class="price-card">
        <view class="price-row">
          <text class="price-label">商品总额</text>
          <text class="price-value">{{ formatPrice(subtotal) }}</text>
        </view>
        <view class="price-row">
          <text class="price-label">运费</text>
          <text class="price-value">{{ freight > 0 ? formatPrice(freight) : '免运费' }}</text>
        </view>
        <view v-if="userStore.isLoggedIn && discountAmount > 0" class="price-row">
          <text class="price-label">会员折扣 (-{{ discountPercent }}%)</text>
          <text class="price-value price-discount">-{{ formatPrice(discountAmount) }}</text>
        </view>
        <view class="price-row price-row--total">
          <text class="price-label">合计</text>
          <text class="price-value price-total">{{ formatPrice(finalTotal) }}</text>
        </view>
      </view>

      <!-- Bottom Spacer -->
      <view class="bottom-spacer" />
    </template>

    <!-- Fixed Bottom Bar -->
    <view v-if="checkoutItems.length > 0" class="bottom-bar">
      <view class="bottom-total">
        <text>合计：</text>
        <text class="bottom-total-price">{{ formatPrice(finalTotal) }}</text>
      </view>
      <view class="btn-submit" :class="{ disabled: submitting }" @tap="submitOrder">
        <text>{{ submitting ? '提交中...' : '提交订单' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import EmptyState from '../../components/EmptyState.vue'
import { createOrder } from '../../api/orders'
import { getAddressList } from '../../api/address'
import type { Address } from '../../api/address'
import { useUserStore } from '../../stores/user'
import { useCartStore } from '../../stores/cart'
import {
  formatPrice,
  showSuccess,
  showError,
  showLoading,
  hideLoading,
  maskPhone,
} from '../../utils/index'

const userStore = useUserStore()
const cartStore = useCartStore()

const addresses = ref<Address[]>([])
const selectedAddress = ref<Address | null>(null)
const remark = ref('')
const paymentMethod = ref('wechat')
const submitting = ref(false)
const loading = ref(true)

// Items from cart or passed from product detail page
const checkoutItems = ref<any[]>([])

// ── Computed: Price ──────────────────────────────
const subtotal = computed(() =>
  checkoutItems.value.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0)
)

const freight = computed(() => (subtotal.value >= 99 ? 0 : 8))

const discountPercent = computed(() =>
  Math.round((1 - userStore.discountRate) * 100)
)

const discountAmount = computed(() =>
  parseFloat((subtotal.value * (1 - userStore.discountRate)).toFixed(2))
)

const finalTotal = computed(() =>
  parseFloat(
    Math.max(0, subtotal.value + freight.value - discountAmount.value).toFixed(2)
  )
)

// ── Data Loading ─────────────────────────────────
async function loadAddresses() {
  try {
    const res = await getAddressList()
    addresses.value = res.data
    selectedAddress.value =
      addresses.value.find((a) => a.is_default) || addresses.value[0] || null
  } catch {
    // Address loading is non-critical
  }
}

onLoad((options: any) => {
  // Get items from cart store or from direct buy via page params / globalData
  const cartItems = cartStore.getCheckoutItems()
  if (cartItems.length) {
    checkoutItems.value = cartItems
  } else {
    const app = getApp() as any
    if (app.globalData?.directBuyItem) {
      const item = app.globalData.directBuyItem
      checkoutItems.value = [
        {
          productId: item.productId || item.product_id,
          productName: item.productName || item.product_name,
          productImage: item.productImage || item.product_image || '',
          spec: item.spec || '',
          unitPrice: item.unitPrice || item.unit_price || 0,
          quantity: item.quantity || 1,
        },
      ]
    } else {
      checkoutItems.value = []
    }
  }

  loadAddresses().finally(() => {
    loading.value = false
  })
})

// ── Address Selection ────────────────────────────
function selectAddress() {
  if (addresses.value.length) {
    uni.showActionSheet({
      itemList: addresses.value.map(
        (a) => `${a.name} ${a.province}${a.city}${a.district}`
      ),
      success: (res) => {
        selectedAddress.value = addresses.value[res.tapIndex]
      },
    })
  } else {
    uni.navigateTo({ url: '/pages/mine/address' })
  }
}

// ── Submit Order ─────────────────────────────────
async function submitOrder() {
  if (!selectedAddress.value) {
    showError('请选择收货地址')
    return
  }
  if (!checkoutItems.value.length) {
    showError('暂无商品')
    return
  }
  if (submitting.value) return

  const confirmed = await new Promise<boolean>((resolve) => {
    uni.showModal({
      title: '确认下单',
      content: `合计：${formatPrice(finalTotal.value)}，确认提交？`,
      success: (r) => resolve(r.confirm),
    })
  })
  if (!confirmed) return

  submitting.value = true
  showLoading('提交中...')

  try {
    const addr = selectedAddress.value!
    const res = await createOrder({
      items: checkoutItems.value.map((item: any) => ({
        product_id: item.productId,
        name: item.productName || '',
        qty: item.quantity,
        unit_price: item.unitPrice,
        subtotal: parseFloat((item.unitPrice * item.quantity).toFixed(2)),
      })),
      payment_method: paymentMethod.value,
      remark: remark.value || undefined,
      receiver_name: addr.name,
      receiver_phone: addr.phone,
      receiver_address: `${addr.province}${addr.city}${addr.district}${addr.detail}`,
    })

    hideLoading()
    cartStore.removeCheckedItems()
    showSuccess('下单成功')

    setTimeout(() => {
      uni.redirectTo({ url: `/pages/order/detail?id=${res.data.id}` })
    }, 1500)
  } catch (err: any) {
    hideLoading()
    showError(err.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

function goShopping() {
  uni.switchTab({ url: '/pages/products/index' })
}
</script>

<style scoped>
.checkout-page {
  min-height: 100vh;
  background-color: #FFF8F0;
}

/* ── Address Card ── */
.address-card {
  background-color: #FFFFFF;
  border-radius: 16px;
  margin: 20rpx 24rpx;
  padding: 28rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.address-content {
  display: flex;
  align-items: flex-start;
}

.addr-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
  margin-top: 4rpx;
}

.addr-info {
  flex: 1;
}

.addr-contact {
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
}

.addr-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #4a3728;
  margin-right: 24rpx;
}

.addr-phone {
  font-size: 26rpx;
  color: #7a6a5a;
}

.addr-full {
  font-size: 26rpx;
  color: #4a3728;
  line-height: 1.5;
}

.addr-arrow {
  font-size: 32rpx;
  color: #b0a090;
  flex-shrink: 0;
  margin-left: 16rpx;
  margin-top: 8rpx;
}

.address-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx 0;
}

.addr-empty-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #FF7B7B;
}

/* ── Items Card ── */
.items-card {
  background-color: #FFFFFF;
  border-radius: 16px;
  margin: 0 24rpx 20rpx;
  padding: 24rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid #f5f5f5;
  margin-bottom: 8rpx;
}

.items-header-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
}

.items-count {
  font-size: 24rpx;
  color: #7a6a5a;
}

.item-row {
  display: flex;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.item-row:last-child {
  border-bottom: none;
}

.item-img {
  width: 140rpx;
  height: 140rpx;
  border-radius: 12px;
  flex-shrink: 0;
}

.item-img-placeholder {
  width: 140rpx;
  height: 140rpx;
  border-radius: 12px;
  flex-shrink: 0;
}

.img-ph--0 { background-color: #FFE0E0; }
.img-ph--1 { background-color: #E0F0FF; }
.img-ph--2 { background-color: #E0F8E8; }
.img-ph--3 { background-color: #FFFDE0; }

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
}

.item-price-row {
  display: flex;
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

/* ── Remark Card ── */
.remark-card {
  background-color: #FFFFFF;
  border-radius: 16px;
  margin: 0 24rpx 20rpx;
  padding: 24rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  position: relative;
}

.remark-label {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
  display: block;
  margin-bottom: 16rpx;
}

.remark-input {
  width: 100%;
  min-height: 100rpx;
  font-size: 26rpx;
  color: #4a3728;
  line-height: 1.6;
  padding: 12rpx;
  background-color: #FFF8F0;
  border-radius: 8px;
  box-sizing: border-box;
}

.remark-count {
  font-size: 22rpx;
  color: #b0a090;
  text-align: right;
  display: block;
  margin-top: 8rpx;
}

/* ── Payment Card ── */
.payment-card {
  background-color: #FFFFFF;
  border-radius: 16px;
  margin: 0 24rpx 20rpx;
  padding: 24rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
  display: block;
  margin-bottom: 20rpx;
}

.payment-option {
  display: flex;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.payment-option:last-child {
  border-bottom: none;
}

.radio {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 2rpx solid #f0e0d0;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.radio.checked {
  border-color: #FF7B7B;
  background-color: #FF7B7B;
}

.method-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
}

.method-label {
  font-size: 28rpx;
  color: #4a3728;
}

/* ── Price Card ── */
.price-card {
  background-color: #FFFFFF;
  border-radius: 16px;
  margin: 0 24rpx 20rpx;
  padding: 24rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.price-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10rpx 0;
}

.price-row--total {
  border-top: 1rpx solid #f0e0d0;
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

.price-discount {
  color: #A8D8B9;
}

.price-total {
  font-size: 36rpx;
  font-weight: 700;
  color: #FF7B7B;
}

/* ── Bottom Bar ── */
.bottom-spacer {
  height: 140rpx;
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #FFFFFF;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.04);
  z-index: 100;
}

.bottom-total {
  display: flex;
  align-items: baseline;
  font-size: 28rpx;
  color: #4a3728;
}

.bottom-total-price {
  font-size: 36rpx;
  font-weight: 700;
  color: #FF7B7B;
}

.btn-submit {
  padding: 16rpx 48rpx;
  border-radius: 50rpx;
  background-color: #FF7B7B;
}

.btn-submit.disabled {
  opacity: 0.6;
}

.btn-submit text {
  font-size: 30rpx;
  font-weight: 600;
  color: #FFFFFF;
}
</style>
