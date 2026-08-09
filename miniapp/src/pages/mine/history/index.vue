<template>
  <view class="history-page">
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
        description="登录后即可查看浏览记录"
        :showButton="true"
        buttonText="去登录"
        @buttonClick="goToLogin"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: EMPTY -->
    <!-- ================================================================ -->
    <template v-else-if="pageState === 'content' && historyItems.length === 0">
      <EmptyState
        icon="👁"
        title="暂无浏览记录"
        description="浏览过的商品将会出现在这里"
        :showButton="true"
        buttonText="去逛逛"
        @buttonClick="goToProducts"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: CONTENT -->
    <!-- ================================================================ -->
    <template v-else-if="pageState === 'content'">
      <view class="history-header">
        <text class="history-header__count">共 {{ totalCount }} 条记录</text>
        <view
          v-if="historyItems.length > 0"
          class="history-header__clear"
          @tap="onClearAll"
        >
          <text class="history-header__clear-text">清空记录</text>
        </view>
      </view>

      <scroll-view
        class="history-scroll"
        :scroll-y="true"
        :style="{ height: scrollHeight + 'px' }"
        @scrolltolower="onLoadMore"
      >
        <view
          v-for="item in historyItems"
          :key="item.product_id"
          class="history-item"
          @tap="goToDetail(item.product_id)"
        >
          <!-- Product Image -->
          <view class="history-item__img-wrap">
            <image
              v-if="item.image && !imageErrors[item.product_id]"
              class="history-item__image"
              :src="item.image"
              mode="aspectFill"
              @error="onImageError(item.product_id)"
            />
            <view v-else class="history-item__image-fallback">
              <text class="history-item__image-emoji">📦</text>
            </view>
          </view>

          <!-- Info -->
          <view class="history-item__info">
            <text class="history-item__name">{{ item.name }}</text>
            <view class="history-item__price-row">
              <text class="history-item__price">{{ formatPriceRange(item.price_min, item.price_max) }}</text>
            </view>
            <text class="history-item__time">{{ getRelativeTime(item.viewed_at) }}</text>
          </view>

          <!-- Delete Button -->
          <view
            class="history-item__delete"
            @tap.stop="onRemoveItem(item)"
          >
            <text class="history-item__delete-icon">🗑</text>
          </view>
        </view>

        <!-- Load More -->
        <view v-if="loadingMore" class="history-load-more">
          <text class="history-load-more__text">加载中...</text>
        </view>
        <view v-else-if="hasMore === false && historyItems.length > 0" class="history-load-more">
          <text class="history-load-more__text history-load-more__text--done">— 没有更多了 —</text>
        </view>

        <!-- Bottom spacer -->
        <view class="history-list-spacer" />
      </scroll-view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import PageLoading from '../../../components/PageLoading.vue'
import EmptyState from '../../../components/EmptyState.vue'
import { useUserStore } from '../../../stores/user'
import { getHistory, removeHistory, clearHistory } from '../../../api/history'
import type { HistoryItemOut } from '../../../api/history'
import { formatPrice, getRelativeTime } from '../../../utils'

const userStore = useUserStore()

// ── Page State ──────────────────────────────────────────────────────────────
type PageState = 'loading' | 'error' | 'content'
const pageState = ref<PageState>('loading')

// ── Data ────────────────────────────────────────────────────────────────────
const historyItems = ref<HistoryItemOut[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = 20
const hasMore = ref<boolean | null>(null)
const loadingMore = ref(false)

// ── Layout ──────────────────────────────────────────────────────────────────
const scrollHeight = computed(() => {
  try {
    const info = uni.getSystemInfoSync()
    const windowHeight = info.windowHeight || 667
    // Header bar: ~90rpx → ~45px (at 2x), status bar ~0-44px
    const headerPx = 50
    return windowHeight - headerPx - (info.statusBarHeight || 0)
  } catch {
    return 600
  }
})

// ── Image Error Fallback ─────────────────────────────────────────────────────
const imageErrors = reactive<Record<string, boolean>>({})
function onImageError(productId: string): void {
  imageErrors[productId] = true
}

// ── Price Range Formatting ──────────────────────────────────────────────────
function formatPriceRange(min: number | null, max: number | null): string {
  if (min == null && max == null) return '价格待定'
  if (min == null) return formatPrice(max!)
  if (max == null) return formatPrice(min)
  if (min === max) return formatPrice(min)
  return `${formatPrice(min)} - ${formatPrice(max)}`
}

// ── Data Loading ────────────────────────────────────────────────────────────
async function loadHistory(reset: boolean = true): Promise<void> {
  if (reset) {
    pageState.value = 'loading'
    currentPage.value = 1
    hasMore.value = null
  }

  // For load-more, compute the next page before the request so that on failure
  // currentPage is never left in a permanently-skipped state.
  const requestPage = reset ? currentPage.value : currentPage.value + 1

  try {
    const res = await getHistory({ page: requestPage, page_size: pageSize })
    const data = res.data

    if (reset) {
      historyItems.value = data.items
    } else {
      historyItems.value = [...historyItems.value, ...data.items]
      // Only commit the page increment on success — prevents permanent skip on failure.
      currentPage.value = requestPage
    }

    totalCount.value = data.total
    hasMore.value = currentPage.value * pageSize < data.total
    pageState.value = 'content'
  } catch {
    if (reset) {
      pageState.value = 'error'
    } else {
      // Load-more failure: silently keep previous data; currentPage unchanged.
      uni.showToast({ title: '加载失败，请重试', icon: 'none', duration: 2000 })
    }
  } finally {
    loadingMore.value = false
  }
}

async function retryLoad(): Promise<void> {
  if (!userStore.isLoggedIn) {
    pageState.value = 'content'
    return
  }
  await loadHistory(true)
}

async function onLoadMore(): Promise<void> {
  if (!userStore.isLoggedIn) return
  if (loadingMore.value) return
  if (hasMore.value === false) return

  loadingMore.value = true
  // currentPage increment moved into loadHistory(false) success path
  // to prevent permanent page-skip on API failure.
  await loadHistory(false)
}

// ── Remove Single Item ──────────────────────────────────────────────────────
function onRemoveItem(item: HistoryItemOut): void {
  uni.showModal({
    title: '删除记录',
    content: `确定要删除「${item.name}」的浏览记录吗？`,
    confirmText: '删除',
    confirmColor: '#FF7B7B',
    success: async (res) => {
      if (res.confirm) {
        try {
          await removeHistory(item.product_id)
          historyItems.value = historyItems.value.filter(
            (h) => h.product_id !== item.product_id
          )
          totalCount.value = Math.max(0, totalCount.value - 1)
          uni.showToast({ title: '已删除', icon: 'success', duration: 1500 })
        } catch {
          uni.showToast({ title: '删除失败，请重试', icon: 'none', duration: 2000 })
        }
      }
    },
  })
}

// ── Clear All ───────────────────────────────────────────────────────────────
function onClearAll(): void {
  if (historyItems.value.length === 0) return
  uni.showModal({
    title: '清空记录',
    content: '确定要清空所有浏览记录吗？此操作不可撤销。',
    confirmText: '清空',
    confirmColor: '#FF7B7B',
    success: async (res) => {
      if (res.confirm) {
        try {
          await clearHistory()
          historyItems.value = []
          totalCount.value = 0
          hasMore.value = null
          uni.showToast({ title: '已清空', icon: 'success', duration: 1500 })
        } catch {
          uni.showToast({ title: '操作失败，请重试', icon: 'none', duration: 2000 })
        }
      }
    },
  })
}

// ── Navigation ──────────────────────────────────────────────────────────────
function goToDetail(productId: string): void {
  uni.navigateTo({ url: `/pages/products/detail?id=${productId}` })
}

function goToLogin(): void {
  uni.switchTab({ url: '/pages/mine/index' })
}

function goToProducts(): void {
  uni.switchTab({ url: '/pages/products/index' })
}

// ── Lifecycle ───────────────────────────────────────────────────────────────
onShow(() => {
  if (!userStore.isLoggedIn) {
    pageState.value = 'content'
    return
  }
  loadHistory(true)
})
</script>

<style scoped>
.history-page {
  min-height: 100vh;
  background: #FFF8F0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ========================================================================== */
/*  HEADER                                                                     */
/* ========================================================================== */
.history-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
}

.history-header__count {
  font-size: 24rpx;
  color: #7a6a5a;
}

.history-header__clear {
  padding: 8rpx 20rpx;
}

.history-header__clear-text {
  font-size: 24rpx;
  color: #FF7B7B;
  font-weight: 500;
}

/* ========================================================================== */
/*  SCROLL AREA                                                                */
/* ========================================================================== */
.history-scroll {
  padding: 0 20rpx;
}

.history-list-spacer {
  height: 40rpx;
}

/* ========================================================================== */
/*  HISTORY ITEM CARD                                                          */
/* ========================================================================== */
.history-item {
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
.history-item__img-wrap {
  width: 160rpx;
  height: 160rpx;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  background: #f5f0eb;
}

.history-item__image {
  width: 100%;
  height: 100%;
}

.history-item__image-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5ebe0, #faf5f0);
}

.history-item__image-emoji {
  font-size: 56rpx;
  line-height: 1;
}

/* Info */
.history-item__info {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.history-item__name {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 8rpx;
}

.history-item__price-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 6rpx;
}

.history-item__price {
  font-size: 30rpx;
  font-weight: 600;
  color: #FF7B7B;
}

.history-item__time {
  font-size: 22rpx;
  color: #7a6a5a;
  line-height: 1.3;
}

/* Delete Button */
.history-item__delete {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.history-item__delete-icon {
  font-size: 32rpx;
  line-height: 1;
}

/* ========================================================================== */
/*  LOAD MORE                                                                  */
/* ========================================================================== */
.history-load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
}

.history-load-more__text {
  font-size: 24rpx;
  color: #7a6a5a;
}

.history-load-more__text--done {
  color: #bfb0a0;
}
</style>
