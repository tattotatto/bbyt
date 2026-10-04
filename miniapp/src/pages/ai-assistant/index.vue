<template>
  <view class="chat-page">
    <!-- ① 品牌色自定义导航：返回 + 客服头像 + 名称 + 在线状态。
         返回键不是可选项：这一页底栏是隐藏的（spec §2 #12），而 switchTab
         会清空页面栈 —— 栈里永远只有聊天页自己，左滑返回也无效。
         少了它，用户点进来就出不去。 -->
    <view class="chat-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="chat-header__inner">
        <view class="chat-header__back" @tap="goHome">
          <AppIcon name="arrow-left" :size="40" tone="white" />
        </view>
        <view class="chat-header__avatar">
          <AppIcon name="kefu-ermai" :size="40" tone="white" />
        </view>
        <view class="chat-header__info">
          <text class="chat-header__name">蓓贝客服</text>
          <text class="chat-header__status">
            {{ connected ? '● 在线 · 通常 1 分钟内回复' : '连接中…' }}
          </text>
        </view>
      </view>
    </view>

    <!-- ② 消息区。底部要让开「快捷问题条 + 输入栏」两行 -->
    <scroll-view
      class="chat-messages"
      scroll-y
      :scroll-into-view="scrollToId"
      :style="{ top: headerHeight + 'px', bottom: bodyBottom + 'px' }"
    >
      <view v-if="messages.length === 0" class="chat-welcome">
        <view class="chat-welcome__avatar">
          <AppIcon name="kefu-ermai" :size="96" tone="white" />
        </view>
        <text class="chat-welcome__title">蓓贝客服</text>
        <text class="chat-welcome__slogan">想问什么都可以，下面挑一条也行</text>
      </view>

      <view v-for="msg in messages" :key="msg.id" :id="'msg-' + msg.id">
        <!-- Thinking indicator -->
        <view v-if="msg.type === 'thinking'" class="chat-thinking">
          <text class="chat-thinking__text">{{ msg.content }}</text>
        </view>

        <!-- Error -->
        <view v-else-if="msg.type === 'error'" class="chat-error">
          <AppIcon name="empty-wifi" :size="28" tone="muted" />
          <text class="chat-error__text">{{ msg.content }}</text>
        </view>

        <!-- Product cards -->
        <view v-else-if="msg.type === 'product_card'" class="chat-products">
          <text v-if="msg.content" class="chat-products__msg">{{ msg.content }}</text>
          <scroll-view scroll-x class="chat-products__list">
            <view
              v-for="(p, idx) in msg.products"
              :key="idx"
              class="chat-product-card"
              @tap="onProductTap(p)"
            >
              <image :src="p.image" mode="aspectFill" class="chat-product-card__img" lazy-load />
              <text class="chat-product-card__name">{{ p.name }}</text>
              <view v-if="p.age_range" class="chat-product-card__age">
                <AppIcon name="tags" :size="20" tone="muted" />
                <text class="chat-product-card__age-text">{{ p.age_range }}</text>
              </view>
              <text class="chat-product-card__price">{{ formatPrice(p.price_min) }} - {{ formatPrice(p.price_max) }}</text>
            </view>
          </scroll-view>
        </view>

        <!-- Order confirm -->
        <view v-else-if="msg.type === 'order_confirm'" class="chat-order">
          <view class="chat-order__card">
            <view class="chat-order__title-row">
              <AppIcon name="shopping-cart" :size="32" tone="ink" />
              <text class="chat-order__title">确认订单</text>
            </view>
            <view class="chat-order__item">
              <text>{{ msg.order?.product?.name }}</text>
              <text>×{{ msg.order?.quantity }}件</text>
            </view>
            <view class="chat-order__actions">
              <view class="chat-order__btn chat-order__btn--confirm" @tap="confirmOrder">
                <text>确认下单</text>
              </view>
              <view class="chat-order__btn chat-order__btn--cancel" @tap="sendQuick('取消')">
                <text>取消</text>
              </view>
            </view>
          </view>
        </view>

        <!-- Order result -->
        <view v-else-if="msg.type === 'order_result'" class="chat-order">
          <view class="chat-order__card chat-order__card--success">
            <AppIcon name="checkmark-circle" :size="80" tone="primary" />
            <text class="chat-order__success-title">下单成功！</text>
            <text class="chat-order__no">订单号：{{ msg.order?.order_no }}</text>
          </view>
        </view>

        <!-- Quick replies -->
        <view v-else-if="msg.type === 'quick_replies'" class="chat-quick-replies">
          <view
            v-for="(item, idx) in msg.items"
            :key="idx"
            class="chat-quick-reply"
            @tap="sendQuick(item)"
          >
            <text>{{ item }}</text>
          </view>
        </view>

        <!-- Text bubble -->
        <view
          v-else
          class="chat-bubble"
          :class="msg.isUser ? 'chat-bubble--user' : 'chat-bubble--ai'"
        >
          <text class="chat-bubble__text">{{ msg.content }}</text>
        </view>
      </view>

      <view class="chat-messages__bottom" id="chat-bottom" />
    </scroll-view>

    <!-- ③ 快捷问题，固定在输入栏正上方 -->
    <scroll-view
      class="quick"
      scroll-x
      :show-scrollbar="false"
      enhanced
      :style="{ bottom: inputHeight + 'px' }"
    >
      <view class="quick__inner">
        <view v-for="q in quickQuestions" :key="q" class="quick__item" @tap="sendQuick(q)">
          <text class="quick__label">{{ q }}</text>
        </view>
      </view>
    </scroll-view>

    <!-- ⑤ 输入栏贴底。这一页不挂 .has-custom-tabbar，也不显示底栏 -->
    <view class="chat-input">
      <view class="chat-input__inner">
        <input
          class="chat-input__field"
          v-model="inputValue"
          placeholder="请描述你的问题…"
          confirm-type="send"
          @confirm="onSend"
        />
        <view class="chat-input__send" @tap="onSend">
          <text class="chat-input__send-text">发送</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import { connectChat, sendMessage, disconnectChat } from '@/api/chat'
import { useChatStore } from '@/stores/chat'
import { useAppStore } from '@/stores/app'
import { DEMO_QUICK_QUESTIONS } from '../../mock/demo-data'
import { formatPrice } from '@/utils/index'

const chatStore = useChatStore()
const appStore = useAppStore()

const inputValue = ref('')
const scrollToId = ref('')

const messages = computed(() => chatStore.messages)
const connected = computed(() => chatStore.connected)
const statusBarHeight = computed(() => appStore.statusBarHeight || 44)
const headerHeight = computed(() => statusBarHeight.value + 50)
const inputHeight = computed(() => 70)
const quickHeight = computed(() => 52)
/** 消息区要让开的下沿：输入栏 + 快捷问题条 */
const bodyBottom = computed(() => inputHeight.value + quickHeight.value)

const quickQuestions = ref(DEMO_QUICK_QUESTIONS)

/**
 * 唯一的发送出口。输入框、快捷问题 chips、订单确认都走这里 ——
 * 另开一条路径最容易漏掉「滚到最新一条」，漏了也只是消息发出去了但看不见。
 */
function dispatch(text: string) {
  sendMessage(text)
  scrollToBottom()
}

function onSend() {
  const text = inputValue.value.trim()
  if (!text) return
  dispatch(text)
  inputValue.value = ''
}

function sendQuick(question: string) {
  dispatch(question)
}

function scrollToBottom() {
  nextTick(() => {
    scrollToId.value = 'chat-bottom'
  })
}

/**
 * 回首页。
 *
 * 这一页按 spec §2 #12 不显示底栏，而 `switchTab` 会清空页面栈 ——
 * 聊天页是 tabBar 页，栈里永远只有它自己，左滑返回也无效。所以这个返回键
 * 是用户唯一的出路。
 *
 * 用 `switchTab` 而不是 `utils` 里的 `goBackOrHome()`：后者在「有栈」时走
 * `navigateBack`，而 tabBar 页永远没有栈可回 ——「回首页」才是这里唯一正确的语义。
 */
function goHome() {
  uni.switchTab({ url: '/pages/home/index' })
}

function onProductTap(product: any) {
  uni.navigateTo({ url: `/pages/products/detail?id=${product.id}` })
}

function confirmOrder() {
  dispatch('确认下单')
}

onMounted(() => {
  connectChat()
})

onUnmounted(() => {
  disconnectChat()
})
</script>

<style scoped lang="scss">
.chat-page {
  height: 100vh;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
}

// ── ① 自定义导航 ───────────────────────────────────────
.chat-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: linear-gradient(135deg, #e16531, #f4a97e);
  padding: 0 var(--space-lg) var(--space-md);
}
.chat-header__inner {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  height: 44px;
}
.chat-header__back {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  // 往左压 8px，让图标视觉上贴住屏幕边缘
  margin-left: -8px;
}
.chat-header__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.chat-header__info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}
.chat-header__name {
  color: var(--text-white);
  font-size: var(--font-lg);
  font-weight: var(--font-weight-semibold);
}
.chat-header__status {
  color: rgba(255, 255, 255, 0.8);
  font-size: var(--font-xs);
}

// ── ② 消息区 ───────────────────────────────────────────
.chat-messages {
  position: fixed;
  left: 0;
  right: 0;
  padding: var(--space-md) var(--space-lg);
  overflow-y: auto;
}
.chat-messages__bottom {
  height: var(--space-lg);
}

// 欢迎区
.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px 0;
}
.chat-welcome__avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e16531, #f4a97e);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-md);
}
.chat-welcome__title {
  font-size: var(--font-xl);
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
}
.chat-welcome__slogan {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-top: var(--space-2xs);
}

// 气泡。border-radius 四角顺序：上左 / 上右 / 下右 / 下左。
// 客服在左，尖角在左上 -> 上左置 0；用户在右，尖角在右上 -> 上右置 0（spec §5.4 ②）。
.chat-bubble {
  max-width: 70%;
  margin-bottom: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  display: block;
}
.chat-bubble--ai {
  background: var(--bg-white);
  border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md);
  box-shadow: var(--shadow-card);
  margin-right: auto;
}
.chat-bubble--user {
  background: var(--color-primary);
  border-radius: var(--radius-md) 0 var(--radius-md) var(--radius-md);
  margin-left: auto;
}
.chat-bubble__text {
  font-size: var(--font-base);
  line-height: var(--leading-normal);
  color: var(--text-primary);
}
.chat-bubble--user .chat-bubble__text {
  color: var(--text-white);
}

// 状态行
.chat-thinking {
  text-align: center;
  margin-bottom: var(--space-md);
}
.chat-thinking__text {
  font-size: var(--font-xs);
  color: var(--text-muted);
}
.chat-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2xs);
  margin-bottom: var(--space-md);
}
.chat-error__text {
  font-size: var(--font-sm);
  color: var(--color-danger);
}

// 商品卡
.chat-products {
  margin-bottom: var(--space-md);
}
.chat-products__msg {
  display: block;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
  padding-left: var(--space-2xs);
}
.chat-products__list {
  white-space: nowrap;
  padding-bottom: var(--space-2xs);
}
.chat-product-card {
  display: inline-block;
  width: 200rpx;
  background: var(--bg-white);
  border-radius: var(--radius-md);
  padding: var(--space-xs);
  margin-right: var(--space-sm);
  box-shadow: var(--shadow-card);
}
.chat-product-card__img {
  width: 100%;
  height: 140rpx;
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
}
.chat-product-card__name {
  display: block;
  font-size: var(--font-xs);
  color: var(--text-primary);
  margin-top: var(--space-2xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chat-product-card__age {
  display: flex;
  align-items: center;
  gap: 2rpx;
}
.chat-product-card__age-text {
  font-size: var(--font-xs);
  color: var(--text-muted);
}
.chat-product-card__price {
  display: block;
  font-size: var(--font-sm);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

// 订单卡
.chat-order {
  margin-bottom: var(--space-md);
}
.chat-order__card {
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: var(--shadow-card);
}
.chat-order__card--success {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.chat-order__title-row {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  margin-bottom: var(--space-xs);
}
.chat-order__title {
  font-size: var(--font-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}
.chat-order__item {
  display: flex;
  justify-content: space-between;
  padding: var(--space-xs) 0;
  font-size: var(--font-sm);
  color: var(--text-primary);
  border-top: 1rpx solid var(--border-light);
}
.chat-order__actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}
.chat-order__btn {
  flex: 1;
  padding: var(--space-xs) 0;
  border-radius: var(--radius-pill);
  text-align: center;
  font-size: var(--font-sm);
}
.chat-order__btn--confirm {
  background: var(--color-primary);
  color: var(--text-white);
}
.chat-order__btn--cancel {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}
.chat-order__success-title {
  font-size: var(--font-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-top: var(--space-sm);
}
.chat-order__no {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin-top: var(--space-2xs);
}

// 消息内联快捷回复
.chat-quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
}
.chat-quick-reply {
  padding: var(--space-xs) var(--space-md);
  background: var(--bg-white);
  border: 1rpx solid var(--border-light);
  border-radius: var(--radius-pill);
  font-size: var(--font-sm);
  color: var(--color-primary);
}

// ── ③ 快捷问题条 ───────────────────────────────────────
.quick {
  position: fixed;
  left: 0;
  right: 0;
  width: 100%;
  padding: var(--space-xs) 0;
  background: var(--bg-primary);
}
.quick__inner {
  display: inline-flex;
  gap: var(--space-sm);
  padding: 0 var(--space-lg);
}
.quick__item {
  background: var(--bg-white);
  border-radius: var(--radius-pill);
  padding: 10rpx 24rpx;
  flex-shrink: 0;
}
.quick__label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

// ── ⑤ 输入栏 ───────────────────────────────────────────
.chat-input {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-white);
  border-top: 1rpx solid var(--border-light);
  padding: var(--space-sm) var(--space-lg);
}
.chat-input__inner {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.chat-input__field {
  flex: 1;
  height: 40px;
  background: var(--bg-primary);
  border-radius: var(--radius-pill);
  padding: 0 var(--space-lg);
  font-size: var(--font-base);
  color: var(--text-primary);
}
.chat-input__send {
  width: 60px;
  height: 40px;
  background: var(--color-primary);
  border-radius: var(--radius-pill);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.chat-input__send-text {
  color: var(--text-white);
  font-size: var(--font-sm);
  font-weight: var(--font-weight-semibold);
}
</style>
