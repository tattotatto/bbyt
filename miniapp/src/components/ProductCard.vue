<template>
  <view class="product-card" @tap="handleClick">
    <image
      class="product-card__image"
      :src="product.images && product.images.length ? product.images[0] : ''"
      mode="aspectFill"
    />
    <view class="product-card__body">
      <text class="product-card__name">{{ product.name }}</text>

      <view class="product-card__price-row">
        <text class="product-card__price">
          <template v-if="(product.price_min ?? 0) === (product.price_max ?? 0)">
            ¥{{ formatPrice(product.price_min) }}
          </template>
          <template v-else>
            ¥{{ formatPrice(product.price_min) }} - ¥{{ formatPrice(product.price_max) }}
          </template>
        </text>
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

function formatPrice(price: number | null): string {
  return (price ?? 0).toFixed(2)
}

function handleClick() {
  emit('click', props.product.id)
}
</script>

<style scoped>
.product-card {
  border-radius: 20px;
  background: #ffffff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

.product-card__image {
  width: 100%;
  height: 200px;
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
}

.product-card__price {
  font-size: 32rpx;
  font-weight: 700;
  color: #FF7B7B;
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
  color: #FF7B7B;
}

.product-card__stock--good {
  color: #A8D8B9;
}
</style>
