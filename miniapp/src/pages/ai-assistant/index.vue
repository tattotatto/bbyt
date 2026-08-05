<template>
  <view class="chat-page">
    <!-- Header -->
    <view class="chat-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="chat-header__inner">
        <view class="chat-header__avatar">
          <text class="chat-header__avatar-emoji">☀️</text>
        </view>
        <view class="chat-header__info">
          <text class="chat-header__name">小暖</text>
          <text class="chat-header__status">{{ connected ? '在线' : '连接中...' }}</text>
        </view>
      </view>
    </view>

    <!-- Messages -->
    <scroll-view
      class="chat-messages"
      scroll-y
      :scroll-into-view="scrollToId"
      :style="{ top: headerHeight + 'px', bottom: inputHeight + 'px' }"
    >
      <view v-if="messages.length === 0" class="chat-welcome">
        <view class="chat-welcome__avatar">
          <text class="chat-welcome__emoji">☀️</text>
        </view>
        <text class="chat-welcome__title">小暖</text>
        <text class="chat-welcome__slogan">给孩子温柔的呵护</text>
        <view class="chat-welcome__hints">
          <text class="chat-welcome__hint">💬 试试问：</text>
          <text class="chat-welcome__hint">"推荐几款3-6岁宝宝的游泳圈"</text>
          <text class="chat-welcome__hint">"有没有温和的儿童防晒霜"</text>
        </view>
      </view>

      <view v-for="msg in messages" :key="msg.id" :id="'msg-' + msg.id">
        <!-- Thinking indicator -->
        <view v-if="msg.type === 'thinking'" class="chat-thinking">
          <text class="chat-thinking__text">{{ msg.content }}</text>
        </view>

        <!-- Error -->
        <view v-else-if="msg.type === 'error'" class="chat-error">
          <text>⚠️ {{ msg.content }}</text>
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
              <text class="chat-product-card__age" v-if="p.age_range">🏷️ {{ p.age_range }}</text>
              <text class="chat-product-card__price">{{ formatPrice(p.price_min) }} - {{ formatPrice(p.price_max) }}</text>
            </view>
          </scroll-view>
        </view>

        <!-- Order confirm -->
        <view v-else-if="msg.type === 'order_confirm'" class="chat-order">
          <view class="chat-order__card">
            <text class="chat-order__title">🛒 确认订单</text>
            <view class="chat-order__item">
              <text>{{ msg.order?.product?.name }}</text>
              <text>×{{ msg.order?.quantity }}件</text>
            </view>
            <view class="chat-order__actions">
              <view class="chat-order__btn chat-order__btn--confirm" @tap="confirmOrder">
                <text>确认下单</text>
              </view>
              <view class="chat-order__btn chat-order__btn--cancel" @tap="sendMessage('取消')">
                <text>取消</text>
              </view>
            </view>
          </view>
        </view>

        <!-- Order result -->
        <view v-else-if="msg.type === 'order_result'" class="chat-order">
          <view class="chat-order__card chat-order__card--success">
            <text class="chat-order__success-icon">✅</text>
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
            @tap="sendMessage(item)"
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

    <!-- Input bar -->
    <view class="chat-input" :style="{ bottom: '0px' }">
      <view class="chat-input__inner">
        <input
          class="chat-input__field"
          v-model="inputValue"
          placeholder="告诉小暖你想找什么..."
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
import { connectChat, sendMessage, disconnectChat } from '@/api/chat'
import { useChatStore } from '@/stores/chat'
import { useAppStore } from '@/stores/app'
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

function onSend() {
  const text = inputValue.value.trim()
  if (!text) return
  sendMessage(text)
  inputValue.value = ''
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    scrollToId.value = 'chat-bottom'
  })
}

function onProductTap(product: any) {
  // 跳转商品详情
  uni.navigateTo({ url: `/pages/products/detail?id=${product.id}` })
}

function confirmOrder() {
  sendMessage('确认下单')
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
  background: #FFF8F0;
  display: flex;
  flex-direction: column;
}

// Header
.chat-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: linear-gradient(135deg, #FF7B7B, #FFA5A5);
  padding: 0 16px 10px;
}
.chat-header__inner {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 44px;
}
.chat-header__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}
.chat-header__avatar-emoji { font-size: 20px; }
.chat-header__name { color: #fff; font-size: 17px; font-weight: 600; }
.chat-header__status { color: rgba(255,255,255,0.8); font-size: 12px; }

// Messages area
.chat-messages {
  position: fixed;
  left: 0;
  right: 0;
  padding: 12px 16px;
  overflow-y: auto;
}
.chat-messages__bottom { height: 20px; }

// Welcome
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
  background: linear-gradient(135deg, #FF7B7B, #FFD93D);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}
.chat-welcome__emoji { font-size: 40px; }
.chat-welcome__title { font-size: 24px; color: #FF7B7B; font-weight: 700; }
.chat-welcome__slogan { font-size: 14px; color: #7a6a5a; margin-bottom: 30px; }
.chat-welcome__hints { width: 100%; }
.chat-welcome__hint {
  display: block;
  padding: 10px 16px;
  margin-bottom: 8px;
  background: #fff;
  border-radius: 12px;
  font-size: 14px;
  color: #4a3728;
}

// Chat bubbles
.chat-bubble {
  max-width: 80%;
  margin-bottom: 12px;
  padding: 12px 16px;
  border-radius: 16px;
  display: inline-block;
}
.chat-bubble--ai {
  background: #fff;
  border-top-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  margin-right: auto;
}
.chat-bubble--user {
  background: #FF7B7B;
  border-top-right-radius: 4px;
  margin-left: auto;
  display: flex;
  justify-content: flex-end;
}
.chat-bubble--user .chat-bubble__text { color: #fff; }
.chat-bubble__text { font-size: 15px; line-height: 1.6; color: #4a3728; }

// Thinking
.chat-thinking {
  text-align: center;
  margin-bottom: 12px;
}
.chat-thinking__text { font-size: 12px; color: #b0a090; }

// Error
.chat-error {
  text-align: center;
  margin-bottom: 12px;
  color: #e74c3c;
  font-size: 13px;
}

// Product cards
.chat-products { margin-bottom: 12px; }
.chat-products__msg {
  display: block;
  font-size: 14px;
  color: #7a6a5a;
  margin-bottom: 8px;
  padding-left: 4px;
}
.chat-products__list {
  white-space: nowrap;
  padding-bottom: 4px;
}
.chat-product-card {
  display: inline-block;
  width: 200rpx;
  background: #fff;
  border-radius: 12px;
  padding: 8px;
  margin-right: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.chat-product-card__img {
  width: 100%;
  height: 140rpx;
  border-radius: 8px;
  background: #f5f0eb;
}
.chat-product-card__name {
  display: block;
  font-size: 13px;
  color: #4a3728;
  margin-top: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chat-product-card__age { font-size: 11px; color: #7EC8E3; display: block; }
.chat-product-card__price { font-size: 14px; color: #FF7B7B; font-weight: 600; display: block; }

// Order confirm/result
.chat-order { margin-bottom: 12px; }
.chat-order__card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.chat-order__card--success { text-align: center; }
.chat-order__title { font-size: 16px; font-weight: 600; color: #4a3728; display: block; margin-bottom: 8px; }
.chat-order__item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
  color: #4a3728;
  border-top: 1px solid #f0e0d0;
}
.chat-order__actions { display: flex; gap: 10px; margin-top: 12px; }
.chat-order__btn { flex: 1; padding: 10px; border-radius: 50px; text-align: center; font-size: 14px; }
.chat-order__btn--confirm { background: #FF7B7B; color: #fff; }
.chat-order__btn--cancel { background: #f5f0eb; color: #7a6a5a; }
.chat-order__success-icon { font-size: 40px; display: block; margin-bottom: 8px; }
.chat-order__success-title { font-size: 18px; font-weight: 600; color: #4a3728; display: block; }
.chat-order__no { font-size: 13px; color: #7a6a5a; display: block; margin-top: 4px; }

// Quick replies
.chat-quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.chat-quick-reply {
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #f0e0d0;
  border-radius: 50px;
  font-size: 14px;
  color: #FF7B7B;
}

// Input bar
.chat-input {
  position: fixed;
  left: 0;
  right: 0;
  background: #fff;
  border-top: 1px solid #f0e0d0;
  padding: 10px 16px;
}
.chat-input__inner {
  display: flex;
  align-items: center;
  gap: 10px;
}
.chat-input__field {
  flex: 1;
  height: 40px;
  background: #FFF8F0;
  border-radius: 20px;
  padding: 0 16px;
  font-size: 15px;
  color: #4a3728;
}
.chat-input__send {
  width: 60px;
  height: 40px;
  background: #FF7B7B;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.chat-input__send-text { color: #fff; font-size: 14px; font-weight: 600; }
</style>
