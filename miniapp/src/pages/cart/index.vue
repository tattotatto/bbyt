<template>
  <view class="cart-page">
    <!-- ================================================================ -->
    <!--  STATE: LOADING -->
    <!-- ================================================================ -->
    <template v-if="pageState === 'loading'">
      <PageLoading type="list" :count="4" />
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
        @buttonClick="retryLoad"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: NOT LOGGED IN -->
    <!-- ================================================================ -->
    <template v-else-if="!userStore.isLoggedIn">
      <EmptyState
        icon="🔐"
        title="请先登录"
        description="登录后即可查看购物车"
        :showButton="true"
        buttonText="去登录"
        @buttonClick="goToLogin"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: EMPTY (logged in, cart has no items) -->
    <!-- ================================================================ -->
    <template v-else-if="cartStore.isEmpty">
      <EmptyState
        icon="🛒"
        title="购物车空空如也"
        description="快去挑选心仪的商品吧"
        :showButton="true"
        buttonText="去逛逛"
        @buttonClick="goToProducts"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: CONTENT -->
    <!-- ================================================================ -->
    <template v-else>
      <!-- Select All Bar -->
      <view class="cart-select-all">
        <view class="cart-select-all__left" @tap="cartStore.toggleAllChecked()">
          <view
            class="cart-checkbox"
            :class="{ 'cart-checkbox--checked': cartStore.isAllChecked }"
          >
            <text v-if="cartStore.isAllChecked" class="cart-checkbox__icon">✓</text>
          </view>
          <text class="cart-select-all__label">全选</text>
        </view>
        <text class="cart-select-all__hint">
          共 {{ cartStore.totalCount }} 件
        </text>
      </view>

      <!-- Cart Item List -->
      <scroll-view
        class="cart-scroll"
        :scroll-y="true"
        :style="{
          height: scrollHeight + 'px',
        }"
      >
        <view
          v-for="item in cartStore.items"
          :key="item.id"
          class="cart-item"
        >
          <!-- Checkbox -->
          <view
            class="cart-checkbox"
            :class="{
              'cart-checkbox--checked': item.checked,
              'cart-checkbox--disabled': isItemLoading(item.id),
            }"
            @tap="onToggleChecked(item.id)"
          >
            <text v-if="item.checked" class="cart-checkbox__icon">✓</text>
          </view>

          <!-- Product Image -->
          <view class="cart-item__img-wrap">
            <image
              v-if="item.productImage && !imageErrors[item.id]"
              class="cart-item__image"
              :src="item.productImage"
              mode="aspectFill"
              @error="onImageError(item.id)"
            />
            <view v-else class="cart-item__image-fallback">
              <text class="cart-item__image-emoji">📦</text>
            </view>
          </view>

          <!-- Info -->
          <view class="cart-item__info">
            <text class="cart-item__name">{{ item.productName }}</text>
            <text v-if="item.spec" class="cart-item__spec">{{ item.spec }}</text>
            <view class="cart-item__bottom">
              <text class="cart-item__price">{{ formatPrice(item.unitPrice) }}</text>
              <!-- Quantity Stepper -->
              <view class="cart-stepper">
                <view
                  class="cart-stepper__btn"
                  :class="{ 'cart-stepper__btn--disabled': item.quantity <= item.minOrderQty || isItemLoading(item.id) }"
                  @tap="onDecrease(item)"
                >
                  <text class="cart-stepper__btn-text">−</text>
                </view>
                <text class="cart-stepper__value">{{ item.quantity }}</text>
                <view
                  class="cart-stepper__btn"
                  :class="{ 'cart-stepper__btn--disabled': item.quantity >= item.stock || isItemLoading(item.id) }"
                  @tap="onIncrease(item)"
                >
                  <text class="cart-stepper__btn-text">+</text>
                </view>
              </view>
            </view>
          </view>

          <!-- Delete -->
          <view
            class="cart-item__delete"
            :class="{ 'cart-item__delete--disabled': isItemLoading(item.id) }"
            @tap="onRemoveItem(item)"
          >
            <text class="cart-item__delete-icon">🗑</text>
          </view>
        </view>

        <!-- Bottom spacer for fixed bar -->
        <view class="cart-list-spacer" />
      </scroll-view>

      <!-- Bottom Checkout Bar -->
      <view class="cart-bottom-bar" :style="{ paddingBottom: safeBottom + 'px' }">
        <view class="cart-bottom-bar__left">
          <text class="cart-bottom-bar__label">已选 {{ cartStore.checkedCount }} 件</text>
          <text class="cart-bottom-bar__total">合计：{{ formatPrice(cartStore.totalPrice) }}</text>
        </view>
        <view
          class="cart-bottom-bar__btn"
          :class="{ 'cart-bottom-bar__btn--disabled': cartStore.checkedCount === 0 }"
          @tap="goToCheckout"
        >
          <text class="cart-bottom-bar__btn-text">去结算</text>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { useCartStore } from '../../stores/cart'
import { useUserStore } from '../../stores/user'
import { useAppStore } from '../../stores/app'
import { formatPrice } from '../../utils'

interface CartItem {
  id: string
  productId: string
  productName: string
  productImage: string
  spec: string
  quantity: number
  unitPrice: number
  stock: number
  minOrderQty: number
  checked: boolean
}

const cartStore = useCartStore()
const userStore = useUserStore()
const appStore = useAppStore()

appStore.init()

// ── Page State ──────────────────────────────────────────────────────────────
type PageState = 'loading' | 'error' | 'content'
const pageState = ref<PageState>('loading')

// ── Layout ──────────────────────────────────────────────────────────────────
const safeBottom = computed(() => Math.max(appStore.safeAreaBottom, 20))

// Cache pixel ratio once (based on 750rpx design width)
const CACHED_PIXEL_RATIO = (() => {
  try {
    const info = uni.getSystemInfoSync()
    return 750 / (info.screenWidth || 375)
  } catch {
    return 2
  }
})()

// Fixed elements height (select-all bar + bottom bar ≈ 200rpx)
const FIXED_HEIGHT_RPX = 200
const scrollHeight = computed(() => {
  const windowHeight = appStore.windowHeight || 667
  const fixedPx = FIXED_HEIGHT_RPX / CACHED_PIXEL_RATIO
  return windowHeight - fixedPx
})

// ── Image Error Fallback ─────────────────────────────────────────────────────
const imageErrors = reactive<Record<string, boolean>>({})
function onImageError(id: string): void {
  imageErrors[id] = true
}

// ── Operation Loading State (prevent double-click races) ────────────────────
const loadingItemIds = ref<Record<string, boolean>>({})

function isItemLoading(id: string): boolean {
  return !!loadingItemIds.value[id]
}

// ── Checkbox Toggle (sync but gate + nextTick prevents rapid re-clicks) ─────
async function onToggleChecked(id: string): Promise<void> {
  if (isItemLoading(id)) return
  loadingItemIds.value = { ...loadingItemIds.value, [id]: true }
  cartStore.toggleChecked(id)
  await nextTick()
  const next = { ...loadingItemIds.value }
  delete next[id]
  loadingItemIds.value = next
}

// ── Data Loading ────────────────────────────────────────────────────────────
async function loadCart(): Promise<void> {
  pageState.value = 'loading'
  if (!userStore.isLoggedIn) {
    pageState.value = 'content'
    return
  }
  try {
    await cartStore.fetch()
    pageState.value = 'content'
  } catch {
    pageState.value = 'error'
  }
}

async function retryLoad(): Promise<void> {
  await loadCart()
}

// ── Quantity Stepper ────────────────────────────────────────────────────────
async function onDecrease(item: CartItem): Promise<void> {
  if (item.quantity <= item.minOrderQty || isItemLoading(item.id)) return
  const newQty = item.quantity - 1
  loadingItemIds.value = { ...loadingItemIds.value, [item.id]: true }
  try {
    await cartStore.updateQuantity(item.id, newQty)
  } finally {
    const next = { ...loadingItemIds.value }
    delete next[item.id]
    loadingItemIds.value = next
  }
}

async function onIncrease(item: CartItem): Promise<void> {
  if (item.quantity >= item.stock || isItemLoading(item.id)) return
  const newQty = item.quantity + 1
  loadingItemIds.value = { ...loadingItemIds.value, [item.id]: true }
  try {
    await cartStore.updateQuantity(item.id, newQty)
  } finally {
    const next = { ...loadingItemIds.value }
    delete next[item.id]
    loadingItemIds.value = next
  }
}

// ── Remove Item ─────────────────────────────────────────────────────────────
function onRemoveItem(item: CartItem): void {
  if (isItemLoading(item.id)) return
  uni.showModal({
    title: '确认删除',
    content: `确定要删除「${item.productName}」吗？`,
    confirmText: '删除',
    confirmColor: '#FF7B7B',
    success: (res) => {
      if (res.confirm) {
        loadingItemIds.value = { ...loadingItemIds.value, [item.id]: true }
        cartStore.removeItem(item.id).finally(() => {
          const next = { ...loadingItemIds.value }
          delete next[item.id]
          loadingItemIds.value = next
        })
      }
    },
  })
}

// ── Navigation ──────────────────────────────────────────────────────────────
function goToLogin(): void {
  uni.switchTab({ url: '/pages/mine/index' })
}

function goToProducts(): void {
  uni.switchTab({ url: '/pages/products/index' })
}

function goToCheckout(): void {
  if (cartStore.checkedCount === 0) return
  uni.navigateTo({ url: '/pages/order/checkout' })
}

// ── Lifecycle ───────────────────────────────────────────────────────────────
onShow(() => {
  loadCart()
})
</script>

<style scoped>
.cart-page {
  min-height: 100vh;
  background: #FFF8F0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ========================================================================== */
/*  SELECT ALL BAR                                                            */
/* ========================================================================== */
.cart-select-all {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  background: #ffffff;
  margin: 20rpx;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.cart-select-all__left {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16rpx;
}

.cart-select-all__label {
  font-size: 28rpx;
  color: #4a3728;
  font-weight: 500;
}

.cart-select-all__hint {
  font-size: 24rpx;
  color: #7a6a5a;
}

/* ========================================================================== */
/*  CHECKBOX                                                                  */
/* ========================================================================== */
.cart-checkbox {
  width: 40rpx;
  height: 40rpx;
  border: 3rpx solid #d4c8b8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.cart-checkbox--checked {
  background: #FF7B7B;
  border-color: #FF7B7B;
}

.cart-checkbox--disabled {
  opacity: 0.5;
  pointer-events: none;
}

.cart-checkbox__icon {
  font-size: 24rpx;
  color: #ffffff;
  font-weight: 700;
  line-height: 1;
}

/* ========================================================================== */
/*  CART SCROLL AREA                                                          */
/* ========================================================================== */
.cart-scroll {
  padding: 0 20rpx;
}

.cart-list-spacer {
  height: 20rpx;
}

/* ========================================================================== */
/*  CART ITEM CARD                                                            */
/* ========================================================================== */
.cart-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  background: #ffffff;
  border-radius: 16px;
  padding: 20rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  gap: 16rpx;
}

/* Image */
.cart-item__img-wrap {
  width: 160rpx;
  height: 160rpx;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  background: #f5f0eb;
}

.cart-item__image {
  width: 100%;
  height: 100%;
}

.cart-item__image-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5ebe0, #faf5f0);
}

.cart-item__image-emoji {
  font-size: 56rpx;
  line-height: 1;
}

/* Info */
.cart-item__info {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.cart-item__name {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cart-item__spec {
  font-size: 22rpx;
  color: #7a6a5a;
  margin-top: 6rpx;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cart-item__bottom {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
}

.cart-item__price {
  font-size: 30rpx;
  font-weight: 600;
  color: #FF7B7B;
}

/* Stepper */
.cart-stepper {
  display: flex;
  flex-direction: row;
  align-items: center;
  border: 2rpx solid #e8e0d8;
  border-radius: 8rpx;
  overflow: hidden;
}

.cart-stepper__btn {
  width: 52rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #faf7f2;
  transition: background 0.15s ease;
}

.cart-stepper__btn--disabled {
  opacity: 0.4;
}

.cart-stepper__btn-text {
  font-size: 32rpx;
  color: #4a3728;
  line-height: 1;
  font-weight: 500;
}

.cart-stepper__value {
  width: 64rpx;
  text-align: center;
  font-size: 26rpx;
  color: #4a3728;
  font-weight: 500;
  background: #ffffff;
}

/* Delete */
.cart-item__delete {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity 0.2s ease;
}

.cart-item__delete--disabled {
  opacity: 0.4;
  pointer-events: none;
}

.cart-item__delete-icon {
  font-size: 32rpx;
  line-height: 1;
}

/* ========================================================================== */
/*  BOTTOM CHECKOUT BAR                                                       */
/* ========================================================================== */
.cart-bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  padding: 16rpx 24rpx;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.06);
  z-index: 100;
}

.cart-bottom-bar__left {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.cart-bottom-bar__label {
  font-size: 24rpx;
  color: #7a6a5a;
}

.cart-bottom-bar__total {
  font-size: 30rpx;
  font-weight: 600;
  color: #FF7B7B;
}

.cart-bottom-bar__btn {
  background: linear-gradient(135deg, #FF7B7B, #FF9B9B);
  border-radius: 50px;
  padding: 16rpx 48rpx;
  transition: opacity 0.2s ease;
}

.cart-bottom-bar__btn--disabled {
  opacity: 0.5;
}

.cart-bottom-bar__btn-text {
  font-size: 30rpx;
  color: #ffffff;
  font-weight: 600;
}
</style>
