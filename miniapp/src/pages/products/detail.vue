<template>
  <view class="product-detail">
    <!-- Loading state -->
    <PageLoading v-if="loading" type="detail" />

    <!-- Error state -->
    <view v-else-if="errorMsg" class="error-state">
      <view class="error-circle">
        <text class="error-circle-icon">!</text>
      </view>
      <text class="error-text">{{ errorMsg }}</text>
      <view class="error-retry" @tap="retry">
        <text class="error-retry-text">重新加载</text>
      </view>
    </view>

    <!-- Empty state: product not found -->
    <EmptyState
      v-else-if="!product"
      icon="📦"
      title="商品不存在"
      description="该商品可能已下架或链接无效"
      :showButton="true"
      buttonText="返回列表"
      @buttonClick="goBack"
    />

    <!-- Main content -->
    <template v-else>
      <!-- Image Swiper -->
      <swiper
        class="detail-swiper"
        indicator-dots
        indicator-color="rgba(255,255,255,0.4)"
        indicator-active-color="#FF7B7B"
        circular
      >
        <swiper-item v-for="(img, idx) in allImages" :key="idx">
          <image
            :src="img"
            mode="aspectFill"
            lazy-load
            class="swiper-img"
          />
        </swiper-item>
        <!-- Fallback gradient slide when no images -->
        <swiper-item v-if="allImages.length === 0">
          <view class="swiper-fallback">
            <text class="swiper-fallback-text">暂无图片</text>
          </view>
        </swiper-item>
      </swiper>

      <!-- Product Info -->
      <view class="info-section">
        <text class="product-name">{{ product.name }}</text>

        <view class="price-row">
          <text class="price-text">
            {{ formatPrice((product as any).price_min ?? product.price_min ?? 0) }}
            <text v-if="(product as any).price_min !== (product as any).price_max"> - {{ formatPrice((product as any).price_max ?? product.price_max ?? 0) }}</text>
          </text>
        </view>

        <view class="tags-row">
          <AgeTag :range="product.age_range ?? ''" size="medium" />
          <CertBadge
            v-for="cert in (product.safety_certifications as any[])"
            :key="cert"
            :name="cert as string"
          />
        </view>

        <view class="meta-row">
          <text class="meta-text">已售{{ (product as any).sales_count ?? 0 }}件</text>
          <text class="meta-divider">·</text>
          <text class="meta-text">库存{{ product.stock ?? 0 }}件</text>
          <text class="meta-divider">·</text>
          <text class="meta-text">{{ (product as any).moq ?? 1 }}件起批</text>
          <text class="meta-divider">·</text>
          <text class="meta-text">{{ (product as any).unit ?? '' }}</text>
        </view>
      </view>

      <!-- Divider -->
      <view class="section-divider" />

      <!-- Specs (if any) -->
      <view v-if="(product.specs as any) && ((product.specs as any).length > 0 || Object.keys(product.specs!).length > 0)" class="spec-section">
        <text class="section-title">规格选择</text>
        <view class="spec-grid">
          <view
            v-for="(spec, si) in ((product.specs as any) as Array<{name: string; options: string[]}>)"
            :key="si"
            class="spec-group"
          >
            <text class="spec-name">{{ spec.name }}</text>
            <view class="spec-options">
              <view
                v-for="(opt, oi) in spec.options"
                :key="oi"
                :class="['spec-pill', { active: selectedSpecs[si] === opt }]"
                @tap="selectSpec(si, opt)"
              >
                {{ opt }}
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- Divider -->
      <view v-if="(product.specs as any) && ((product.specs as any).length > 0 || Object.keys(product.specs!).length > 0)" class="section-divider" />

      <!-- Price Table -->
      <view v-if="(product.price_tiers && product.price_tiers.length > 0) || Object.keys(product.pricing_rules || {}).length > 0" class="section">
        <text class="section-title">批发价格表</text>
        <PriceTable
          :pricingRules="(product.price_tiers as any) || product.pricing_rules"
          :userLevel="userStore.userLevel"
          :qty="quantity"
        />
      </view>

      <!-- Divider -->
      <view class="section-divider" />

      <!-- Quantity Stepper -->
      <view class="section">
        <text class="section-title">购买数量</text>
        <view class="stepper">
          <view
            :class="['stepper-btn', { disabled: quantity <= ((product as any).moq || 1) }]"
            @tap="decreaseQty"
          >
            <text class="stepper-btn-text">−</text>
          </view>
          <input
            class="stepper-input"
            type="number"
            v-model.number="quantity"
          />
          <view
            :class="['stepper-btn', { disabled: quantity >= (product.stock ?? 9999) }]"
            @tap="increaseQty"
          >
            <text class="stepper-btn-text">+</text>
          </view>
        </view>
        <text class="stepper-hint">
          起订{{ (product as any).moq ?? 1 }}{{ (product as any).unit ?? '' }} · 库存{{ product.stock ?? 0 }}{{ (product as any).unit ?? '' }}
        </text>
      </view>

      <!-- Divider -->
      <view class="section-divider" />

      <!-- Description -->
      <view class="section">
        <text class="section-title">商品详情</text>
        <text class="desc-text">{{ product.description }}</text>
        <image
          v-for="(img, i) in (product.detail_images || [])"
          :key="'desc-' + i"
          :src="img"
          mode="widthFix"
          lazy-load
          class="desc-img"
        />
      </view>

      <!-- Bottom spacer for fixed bar -->
      <view class="bottom-spacer" />

      <!-- Fixed Bottom Bar -->
      <view class="bottom-bar">
        <view class="bottom-left">
          <view class="icon-btn" @tap="handleFavorite">
            <text class="icon-btn-emoji">🤍</text>
            <text class="icon-btn-label">收藏</text>
          </view>
          <view class="icon-btn" @tap="goToCart">
            <text class="icon-btn-emoji">🛒</text>
            <text class="icon-btn-label">购物车</text>
            <text v-if="cartStore.totalCount > 0" class="cart-badge">{{ cartStore.totalCount }}</text>
          </view>
        </view>
        <view class="bottom-right">
          <view class="btn-cart" @tap="addToCart">
            <text class="btn-cart-text">加入购物车</text>
          </view>
          <view class="btn-buy" @tap="buyNow">
            <text class="btn-buy-text">立即购买</text>
          </view>
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
import AgeTag from '../../components/AgeTag.vue'
import CertBadge from '../../components/CertBadge.vue'
import PriceTable from '../../components/PriceTable.vue'
import { getProductDetail } from '../../api/products'
import type { ProductDetail } from '../../api/products'
import { useUserStore } from '../../stores/user'
import { useCartStore } from '../../stores/cart'
import { formatPrice, showSuccess, showError } from '../../utils/index'

const userStore = useUserStore()
const cartStore = useCartStore()

// ── State ──────────────────────────────────────────────
const loading = ref(true)
const errorMsg = ref('')
const product = ref<ProductDetail | null>(null)
const quantity = ref(1)
const selectedSpecs = ref<Record<number, string>>({})

// ── All images for swiper ──────────────────────────────
const allImages = computed(() => {
  if (!product.value) return []
  return [
    ...(product.value.images || []),
    ...(product.value.detail_images || [])
  ]
})

// ── Load product detail ────────────────────────────────
async function loadProduct(id: string | number) {
  loading.value = true
  errorMsg.value = ''

  try {
    const res = await getProductDetail(String(id))
    product.value = res.data

    // Set default quantity to MOQ
    quantity.value = (res.data as any).moq || 1

    // Initialize spec selections to first option of each spec
    const specsArr = (res.data.specs as any) as Array<{ name: string; options: string[] }> | null
    if (specsArr && specsArr.length > 0) {
      const initial: Record<number, string> = {}
      specsArr.forEach((spec, idx) => {
        if (spec.options && spec.options.length > 0) {
          initial[idx] = spec.options[0]
        }
      })
      selectedSpecs.value = initial
    }
  } catch (err: any) {
    errorMsg.value = err.message || err.msg || '加载失败'
  } finally {
    loading.value = false
  }
}

// ── Spec selection ─────────────────────────────────────
function selectSpec(specIdx: number, option: string) {
  selectedSpecs.value[specIdx] = option
}

// ── Get formatted selected spec string ─────────────────
function getSelectedSpec(): string {
  const specsArr = (product.value?.specs as any) as Array<{ name: string; options: string[] }> | null | undefined
  if (!specsArr || specsArr.length === 0) {
    return '默认'
  }
  return specsArr
    .map((_s, i) => selectedSpecs.value[i] || '')
    .filter(Boolean)
    .join(' / ') || '默认'
}

// ── Quantity stepper ───────────────────────────────────
function decreaseQty() {
  const moq = (product.value as any)?.moq || 1
  if (quantity.value > moq) {
    quantity.value--
  }
}

function increaseQty() {
  const maxStock = product.value?.stock || 9999
  if (quantity.value < maxStock) {
    quantity.value++
  }
}

// ── Cart actions ───────────────────────────────────────
function addToCart() {
  if (!product.value) return

  cartStore.addItem({
    productId: product.value.id as any,
    productName: product.value.name,
    productImage: product.value.images?.[0] || '',
    spec: getSelectedSpec(),
    unitPrice: (product.value as any).price_min ?? product.value.price_min ?? 0,
    quantity: quantity.value,
    stock: product.value.stock ?? 0,
    minOrderQty: (product.value as any).moq ?? product.value.min_order_qty
  })

  showSuccess('已加入购物车')
}

function buyNow() {
  addToCart()
  uni.navigateTo({ url: '/pages/order/checkout' })
}

// ── Navigation ─────────────────────────────────────────
function goToCart() {
  uni.switchTab({ url: '/pages/cart/index' })
}

function handleFavorite() {
  showSuccess('已收藏')
}

function goBack() {
  uni.navigateBack()
}

function retry() {
  if (product.value) {
    loadProduct(product.value.id)
  }
}

// ── Lifecycle ──────────────────────────────────────────
onLoad((options: any) => {
  const id = options?.id
  if (id) {
    loadProduct(String(id))
  } else {
    errorMsg.value = '商品ID无效'
  }
})
</script>

<style scoped>
.product-detail {
  background: #FFF8F0;
  min-height: 100vh;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ── Swiper ──────────────────────────────────────────── */
.detail-swiper {
  width: 100%;
  height: 600rpx;
}

.swiper-img {
  width: 100%;
  height: 100%;
}

.swiper-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #FFA5A5, #FF7B7B);
}

.swiper-fallback-text {
  font-size: 36rpx;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
}

/* ── Info section ────────────────────────────────────── */
.info-section {
  background: #FFFFFF;
  padding: 24rpx 32rpx;
}

.product-name {
  font-size: 36rpx;
  font-weight: 600;
  color: #4a3728;
  line-height: 1.4;
}

.price-row {
  margin-top: 16rpx;
}

.price-text {
  font-size: 40rpx;
  font-weight: 700;
  color: #FF7B7B;
}

.tags-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12rpx;
  margin-top: 16rpx;
  flex-wrap: wrap;
}

.meta-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-top: 12rpx;
  flex-wrap: wrap;
}

.meta-text {
  font-size: 24rpx;
  color: #7a6a5a;
}

.meta-divider {
  font-size: 24rpx;
  color: #b0a090;
  margin: 0 8rpx;
}

/* ── Section divider ─────────────────────────────────── */
.section-divider {
  height: 16rpx;
  background: #FFF8F0;
}

/* ── Generic section ─────────────────────────────────── */
.section {
  background: #FFFFFF;
  padding: 24rpx 32rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
  display: block;
  margin-bottom: 20rpx;
}

/* ── Spec selection ──────────────────────────────────── */
.spec-section {
  background: #FFFFFF;
  padding: 24rpx 32rpx;
}

.spec-section .section-title {
  margin-bottom: 20rpx;
}

.spec-grid {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.spec-group {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.spec-name {
  font-size: 26rpx;
  font-weight: 500;
  color: #4a3728;
}

.spec-options {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 16rpx;
}

.spec-pill {
  padding: 12rpx 24rpx;
  border: 1px solid #f0e0d0;
  border-radius: 8px;
  background: #FFFFFF;
  font-size: 26rpx;
  color: #4a3728;
}

.spec-pill.active {
  border-color: #FF7B7B;
  background: #FFF0F0;
  color: #FF7B7B;
}

/* ── Quantity stepper ────────────────────────────────── */
.stepper {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0;
}

.stepper-btn {
  width: 72rpx;
  height: 72rpx;
  border: 1px solid #f0e0d0;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stepper-btn:first-child {
  border-radius: 8px 0 0 8px;
}

.stepper-btn:last-child {
  border-radius: 0 8px 8px 0;
}

.stepper-btn.disabled {
  background: #f5f5f5;
  opacity: 0.5;
}

.stepper-btn-text {
  font-size: 36rpx;
  color: #4a3728;
  font-weight: 500;
  line-height: 1;
}

.stepper-input {
  width: 140rpx;
  height: 72rpx;
  border-top: 1px solid #f0e0d0;
  border-bottom: 1px solid #f0e0d0;
  border-left: none;
  border-right: none;
  text-align: center;
  font-size: 28rpx;
  color: #4a3728;
  background: #FFFFFF;
}

.stepper-hint {
  font-size: 22rpx;
  color: #b0a090;
  margin-top: 12rpx;
  display: block;
}

/* ── Description ─────────────────────────────────────── */
.desc-text {
  font-size: 26rpx;
  color: #7a6a5a;
  line-height: 1.8;
  display: block;
  margin-bottom: 24rpx;
}

.desc-img {
  width: 100%;
  display: block;
  margin-bottom: 16rpx;
  border-radius: 12px;
}

/* ── Error state ─────────────────────────────────────── */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 40rpx;
}

.error-circle {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: #FF7B7B;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}

.error-circle-icon {
  font-size: 40rpx;
  font-weight: 700;
  color: #FFFFFF;
}

.error-text {
  font-size: 28rpx;
  color: #7a6a5a;
  text-align: center;
  margin-bottom: 32rpx;
  line-height: 1.5;
}

.error-retry {
  background: #FF7B7B;
  border-radius: 50px;
  padding: 14px 48px;
}

.error-retry-text {
  font-size: 28rpx;
  color: #FFFFFF;
  font-weight: 500;
}

/* ── Bottom spacer ───────────────────────────────────── */
.bottom-spacer {
  height: 140rpx;
}

/* ── Fixed Bottom Bar ────────────────────────────────── */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  background: #FFFFFF;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.04);
  z-index: 100;
}

.bottom-left {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.icon-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20rpx;
  position: relative;
}

.icon-btn-emoji {
  font-size: 36rpx;
  line-height: 1.2;
}

.icon-btn-label {
  font-size: 20rpx;
  color: #7a6a5a;
  margin-top: 4rpx;
}

.cart-badge {
  position: absolute;
  top: -4rpx;
  right: 8rpx;
  min-width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: #FF7B7B;
  color: #FFFFFF;
  font-size: 20rpx;
  line-height: 32rpx;
  text-align: center;
  padding: 0 6rpx;
}

.bottom-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex: 1;
  gap: 16rpx;
}

.btn-cart {
  flex: 1;
  height: 80rpx;
  border-radius: 50px;
  background: #FFD93D;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 32rpx;
}

.btn-cart-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #4a3728;
}

.btn-buy {
  flex: 1;
  height: 80rpx;
  border-radius: 50px;
  background: #FF7B7B;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 32rpx;
}

.btn-buy-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #FFFFFF;
}
</style>
