<template>
  <view class="price-table">
    <!-- Header -->
    <view class="price-table__header">
      <text class="price-table__cell price-table__cell--header">数量范围</text>
      <text class="price-table__cell price-table__cell--header">单价</text>
      <text class="price-table__cell price-table__cell--header price-table__cell--right">总价</text>
    </view>

    <!-- Data rows for current user level -->
    <view
      v-for="(tier, index) in currentLevelTiers"
      :key="index"
      :class="['price-table__row', { 'price-table__row--active': isActiveTier(tier, index) }]"
    >
      <text
        :class="['price-table__cell', { 'price-table__cell--active': isActiveTier(tier, index) }]"
      >
        {{ formatQtyRange(tier, index) }}
      </text>
      <text
        :class="['price-table__cell', { 'price-table__cell--active': isActiveTier(tier, index) }]"
      >
        &yen;{{ formatMoney(tier.price) }}
      </text>
      <text
        :class="[
          'price-table__cell',
          'price-table__cell--right',
          { 'price-table__cell--active': isActiveTier(tier, index) }
        ]"
      >
        &yen;{{ formatMoney(tier.price * qty) }}
      </text>
    </view>

    <!-- Level badge -->
    <view v-if="userLevel" class="price-table__level-badge">
      <text class="price-table__level-text">
        {{ levelLabel }}专享价格
      </text>
    </view>

    <!-- Fallback: no tiers for current level -->
    <view v-if="currentLevelTiers.length === 0" class="price-table__empty">
      <text class="price-table__empty-text">暂无价格信息</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PricingTier } from '../api/types'

interface Props {
  pricingRules: Record<string, PricingTier[]>
  userLevel: string
  qty?: number
}

const props = withDefaults(defineProps<Props>(), {
  qty: 1,
})

const LEVEL_LABELS: Record<string, string> = {
  normal: '普通会员',
  silver: '银卡会员',
  gold: '金卡会员',
  platinum: '钻石会员',
}

const levelLabel = computed(() => {
  return LEVEL_LABELS[props.userLevel] ?? props.userLevel
})

/** Tiers for the current user's level, sorted by qty ascending */
const currentLevelTiers = computed(() => {
  const tiers = props.pricingRules[props.userLevel] ?? []
  return [...tiers].sort((a, b) => a.qty - b.qty)
})

/** Format qty range: "10-49" or "100+" or "10" (single tier) */
function formatQtyRange(tier: PricingTier, index: number): string {
  const nextTier = currentLevelTiers.value[index + 1]
  if (nextTier) {
    const maxQty = nextTier.qty - 1
    if (maxQty === tier.qty) {
      return `${tier.qty}`
    }
    return `${tier.qty}-${maxQty}`
  }
  return `${tier.qty}+`
}

/** Check if user's current qty falls in this tier's range */
function isActiveTier(tier: PricingTier, index: number): boolean {
  if (props.qty < tier.qty) return false
  const nextTier = currentLevelTiers.value[index + 1]
  if (nextTier && props.qty >= nextTier.qty) return false
  return true
}

function formatMoney(price: number): string {
  return price.toFixed(2)
}
</script>

<style scoped>
.price-table {
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.price-table__header {
  display: flex;
  flex-direction: row;
  background: #FFF8F0;
  border-bottom: 1px solid #f0e0d0;
}

.price-table__row {
  display: flex;
  flex-direction: row;
  border-bottom: 1px solid #f0e0d0;
}

.price-table__row:last-of-type {
  border-bottom: none;
}

.price-table__row--active {
  background: #FFF0F0;
}

.price-table__cell {
  flex: 1;
  font-size: 24rpx;
  color: #7a6a5a;
  padding: 12px 16px;
  line-height: 1.4;
}

.price-table__cell--header {
  font-weight: 600;
}

.price-table__cell--right {
  text-align: right;
}

.price-table__cell--active {
  font-weight: 700;
  color: #FF7B7B;
}

.price-table__level-badge {
  padding: 10px 16px;
  background: #FFF8F0;
}

.price-table__level-text {
  font-size: 22rpx;
  color: #FF7B7B;
  font-weight: 500;
}

.price-table__empty {
  padding: 24px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.price-table__empty-text {
  font-size: 24rpx;
  color: #b0a090;
}
</style>
