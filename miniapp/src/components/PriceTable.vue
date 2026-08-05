<template>
  <view class="price-table">
    <!-- Header -->
    <view class="price-table__header">
      <text class="price-table__cell price-table__cell--header">数量范围</text>
      <text class="price-table__cell price-table__cell--header">单价</text>
      <text class="price-table__cell price-table__cell--header price-table__cell--right">总价</text>
    </view>

    <!-- Data rows -->
    <view
      v-for="(rule, index) in pricingRules"
      :key="index"
      :class="['price-table__row', { 'price-table__row--active': isActiveRow(rule) }]"
    >
      <text
        :class="['price-table__cell', { 'price-table__cell--active': isActiveRow(rule) }]"
      >
        {{ rule.min_qty }}-{{ rule.max_qty }}
      </text>
      <text
        :class="['price-table__cell', { 'price-table__cell--active': isActiveRow(rule) }]"
      >
        ¥{{ formatPrice(rule.unit_price) }}
      </text>
      <text
        :class="[
          'price-table__cell',
          'price-table__cell--right',
          { 'price-table__cell--active': isActiveRow(rule) }
        ]"
      >
        ¥{{ formatPrice(rule.unit_price * qty) }}
      </text>
    </view>

    <!-- User level discount note -->
    <view v-if="userLevel > 0" class="price-table__discount">
      <text class="price-table__discount-text">
        您的等级享受{{ discountLabel }}优惠
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface PricingRule {
  min_qty: number
  max_qty: number
  unit_price: number
}

interface Props {
  pricingRules: PricingRule[]
  userLevel?: number
  qty?: number
}

const props = withDefaults(defineProps<Props>(), {
  userLevel: 0,
  qty: 1
})

const discountLabel = computed(() => {
  const discount = Math.max(0, 10 - props.userLevel * 0.5)
  return discount.toFixed(1) + '折'
})

function isActiveRow(rule: PricingRule): boolean {
  return props.qty >= rule.min_qty && props.qty <= rule.max_qty
}

function formatPrice(price: number): string {
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

.price-table__discount {
  padding: 10px 16px;
  background: #FFF8F0;
}

.price-table__discount-text {
  font-size: 22rpx;
  color: #7a6a5a;
}
</style>
