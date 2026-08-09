<template>
  <view class="help-page">
    <view class="faq-card">
      <view
        v-for="(item, index) in faqList"
        :key="index"
        class="faq-item"
        :class="{ 'faq-item--last': index === faqList.length - 1 }"
      >
        <view class="faq-question" @tap="toggleFaq(index)">
          <text class="faq-q-icon">Q</text>
          <text class="faq-q-text">{{ item.question }}</text>
          <text class="faq-arrow" :class="{ 'faq-arrow--open': expandedIndex === index }">
            &#x203A;
          </text>
        </view>
        <view v-if="expandedIndex === index" class="faq-answer">
          <text class="faq-a-text">{{ item.answer }}</text>
        </view>
      </view>
    </view>

    <view class="footer-section">
      <text class="footer-text">更多问题请联系在线客服</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface FaqItem {
  question: string
  answer: string
}

const faqList: FaqItem[] = [
  {
    question: '如何下单？',
    answer: '在商品页面选择心仪的商品，点击「加入购物车」或「立即购买」，进入结算页确认信息后提交订单即可。',
  },
  {
    question: '账期是什么？',
    answer: '账期是指订单确认收货后到实际结算付款的时间周期。不同会员等级享有不同的账期天数，您可在会员中心查看您的账期权益。',
  },
  {
    question: '如何申请退款？',
    answer: '在「我的订单」中找到需要退款的订单，点击进入订单详情，选择「申请退款」并填写退款原因和金额，提交后等待客服审核处理。',
  },
  {
    question: '订单多久会发货？',
    answer: '一般情况下，订单支付确认后 24 小时内安排发货。如遇节假日或大促活动期间，发货时间可能会有所延长，敬请谅解。',
  },
  {
    question: '如何修改收货地址？',
    answer: '在「我的」页面进入「收货地址」，可以添加、编辑或删除收货地址。已提交的订单如需修改地址，请联系客服协助处理。',
  },
]

const expandedIndex = ref<number | null>(null)

function toggleFaq(index: number) {
  if (expandedIndex.value === index) {
    expandedIndex.value = null
  } else {
    expandedIndex.value = index
  }
}
</script>

<style scoped>
.help-page {
  min-height: 100vh;
  background: #FFF8F0;
  padding: 24rpx;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* FAQ Card */
.faq-card {
  background: #ffffff;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.faq-item {
  border-bottom: 1px solid #f5f5f5;
}

.faq-item--last {
  border-bottom: none;
}

.faq-question {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 28rpx 32rpx;
}

.faq-q-icon {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: #FF7B7B;
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  flex-shrink: 0;
  line-height: 1;
}

.faq-q-text {
  flex: 1;
  font-size: 28rpx;
  color: #4a3728;
  line-height: 1.5;
}

.faq-arrow {
  font-size: 28rpx;
  color: #c4b5a5;
  flex-shrink: 0;
  transition: transform 0.2s ease;
  margin-left: 12rpx;
}

.faq-arrow--open {
  transform: rotate(90deg);
}

.faq-answer {
  padding: 0 32rpx 28rpx 92rpx;
}

.faq-a-text {
  font-size: 26rpx;
  color: #7a6a5a;
  line-height: 1.7;
}

/* Footer */
.footer-section {
  display: flex;
  justify-content: center;
  margin-top: 48rpx;
}

.footer-text {
  font-size: 24rpx;
  color: #c4b5a5;
}
</style>
