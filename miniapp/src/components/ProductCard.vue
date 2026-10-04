<template>
  <view class="product-card" @tap="handleClick">
    <image
      v-if="coverImage"
      class="product-card__image"
      :src="coverImage"
      mode="aspectFill"
    />
    <!-- 无图兜底：原来是 <image src=""> —— 商品没图时这里就是一块空白。
         现在给一个照片图标占位，至少说明「这里本该有张图」。 -->
    <view v-else class="product-card__image product-card__image--placeholder">
      <AppIcon name="photo" :size="72" tone="muted" />
    </view>
    <view class="product-card__body">
      <text class="product-card__name">{{ product.name }}</text>

      <view class="product-card__price-row">
        <view class="product-card__price">
          <text class="product-card__currency">¥</text>
          <text class="product-card__amount">{{ priceText }}</text>
        </view>
        <text v-if="moq > 0" class="product-card__moq">{{ moq }}件起批</text>
      </view>

      <view class="product-card__bottom">
        <AgeTag :range="product.age_range ?? ''" size="small" />

        <view class="product-card__badges">
          <text
            v-if="(product.stock ?? 0) > 0 && (product.stock ?? 0) < 50"
            class="product-card__stock product-card__stock--low"
          >
            仅剩{{ product.stock }}件
          </text>
          <text
            v-else-if="(product.stock ?? 0) >= 50"
            class="product-card__stock product-card__stock--good"
          >
            库存充足
          </text>

          <CertBadge
            v-for="(cert, ci) in firstTwoCerts"
            :key="ci"
            :name="cert.name"
          />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'
import AgeTag from './AgeTag.vue'
import CertBadge from './CertBadge.vue'
import type { SafetyCertification } from '../api/products'

interface Product {
  id: string
  name: string
  images: string[]
  age_range: string | null
  price_min: number | null
  price_max: number | null
  stock: number | null
  safety_certifications: SafetyCertification[]
  /**
   * 最低起批量。后端 ProductListOut 里有这个字段（models/product.py
   * 的 min_order_qty，默认 10），商品列表接口返回的就是它。
   * 写成可选是为了不让调用方被迫补字段 —— 不传就不显示「xx件起批」。
   */
  min_order_qty?: number
}

interface Props {
  product: Product
  showStock?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showStock: true
})

const emit = defineEmits<{
  click: [id: string]
}>()

const firstTwoCerts = computed(() => {
  return (props.product.safety_certifications || []).slice(0, 2)
})

const coverImage = computed(() => {
  const images = props.product.images || []
  return images.length ? images[0] : ''
})

/** 起批量。缺字段或为 0 时不显示，避免出现「0件起批」。 */
const moq = computed(() => props.product.min_order_qty ?? 0)

/**
 * 价格文案。与改动前逐字一致（'¥12.00' / '¥12.00 - ¥15.00'）——
 * 只是把开头的「¥」拆成独立的 text，好让它单独用小一号字。
 */
const priceText = computed(() => {
  const min = formatPrice(props.product.price_min)
  const max = formatPrice(props.product.price_max)
  if ((props.product.price_min ?? 0) === (props.product.price_max ?? 0)) return min
  return `${min} - ¥${max}`
})

function formatPrice(price: number | null): string {
  return (price ?? 0).toFixed(2)
}

function handleClick() {
  emit('click', props.product.id)
}
</script>

<style scoped>
.product-card {
  border-radius: var(--radius-lg);
  background: var(--bg-white);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

.product-card__image {
  width: 100%;
  height: 200px;
}

.product-card__image--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-muted);
}

.product-card__body {
  padding: 16px;
}

.product-card__name {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 78rpx;
}

.product-card__price-row {
  margin-top: 8px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.product-card__price {
  display: flex;
  align-items: baseline;
  color: var(--color-primary);
}

/* 「¥」小一号，让数字本身更突出 */
.product-card__currency {
  font-size: var(--font-sm);
  font-weight: 700;
}

.product-card__amount {
  font-size: var(--font-xl);
  font-weight: 700;
}

.product-card__moq {
  font-size: var(--font-xs);
  color: var(--text-muted);
}

.product-card__bottom {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.product-card__badges {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.product-card__stock {
  font-size: 22rpx;
  margin-right: 8px;
}

.product-card__stock--low {
  color: var(--color-primary);
}

.product-card__stock--good {
  color: #A8D8B9;
}
</style>
