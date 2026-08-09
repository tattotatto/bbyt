<template>
  <view class="favorites-page">
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
        description="登录后即可查看收藏夹"
        :showButton="true"
        buttonText="去登录"
        @buttonClick="goToLogin"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: EMPTY -->
    <!-- ================================================================ -->
    <template v-else-if="pageState === 'content' && favorites.length === 0">
      <EmptyState
        icon="💖"
        title="收藏夹空空如也"
        description="快去挑选心仪的商品吧"
        :showButton="true"
        buttonText="去逛逛"
        @buttonClick="goToProducts"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: CONTENT -->
    <!-- ================================================================ -->
    <template v-else-if="pageState === 'content'">
      <view class="favorites-header">
        <text class="favorites-header__count">共 {{ totalCount }} 件收藏</text>
      </view>

      <scroll-view
        class="favorites-scroll"
        :scroll-y="true"
        :style="{ height: scrollHeight + 'px' }"
        @scrolltolower="onLoadMore"
      >
        <view
          v-for="item in favorites"
          :key="item.product_id"
          class="favorite-item"
          @tap="goToDetail(item.product_id)"
        >
          <!-- Product Image -->
          <view class="favorite-item__img-wrap">
            <image
              v-if="item.image && !imageErrors[item.product_id]"
              class="favorite-item__image"
              :src="item.image"
              mode="aspectFill"
              @error="onImageError(item.product_id)"
            />
            <view v-else class="favorite-item__image-fallback">
              <text class="favorite-item__image-emoji">📦</text>
            </view>
          </view>

          <!-- Info -->
          <view class="favorite-item__info">
            <text class="favorite-item__name">{{ item.name }}</text>
            <view class="favorite-item__price-row">
              <text class="favorite-item__price">{{ formatPriceRange(item.price_min, item.price_max) }}</text>
            </view>
            <text class="favorite-item__time">{{ formatDate(item.created_at) }}</text>
          </view>

          <!-- Remove Button -->
          <view
            class="favorite-item__remove"
            @tap.stop="onRemoveFavorite(item)"
          >
            <text class="favorite-item__remove-icon">♥</text>
          </view>
        </view>

        <!-- Load More -->
        <view v-if="loadingMore" class="favorites-load-more">
          <text class="favorites-load-more__text">加载中...</text>
        </view>
        <view v-else-if="hasMore === false && favorites.length > 0" class="favorites-load-more">
          <text class="favorites-load-more__text favorites-load-more__text--done">— 没有更多了 —</text>
        </view>

        <!-- Bottom spacer -->
        <view class="favorites-list-spacer" />
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
import { getFavorites, removeFavorite } from '../../../api/favorites'
import type { FavoriteItemOut } from '../../../api/favorites'
import { formatPrice, formatDate } from '../../../utils'

const userStore = useUserStore()

// ── Page State ──────────────────────────────────────────────────────────────
type PageState = 'loading' | 'error' | 'content'
const pageState = ref<PageState>('loading')

// ── Data ────────────────────────────────────────────────────────────────────
const favorites = ref<FavoriteItemOut[]>([])
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
async function loadFavorites(reset: boolean = true): Promise<void> {
  if (reset) {
    pageState.value = 'loading'
    currentPage.value = 1
    hasMore.value = null
  }

  if (!userStore.isLoggedIn) {
    pageState.value = 'content'
    return
  }

  try {
    const res = await getFavorites({ page: currentPage.value, page_size: pageSize })
    const data = res.data

    if (reset) {
      favorites.value = data.items
    } else {
      favorites.value = [...favorites.value, ...data.items]
    }

    totalCount.value = data.total
    hasMore.value = currentPage.value * pageSize < data.total
    pageState.value = 'content'
  } catch {
    if (reset) {
      pageState.value = 'error'
    } else {
      // Load-more failure: silently keep previous data
      uni.showToast({ title: '加载失败，请重试', icon: 'none', duration: 2000 })
    }
  } finally {
    loadingMore.value = false
  }
}

async function retryLoad(): Promise<void> {
  await loadFavorites(true)
}

async function onLoadMore(): Promise<void> {
  if (loadingMore.value) return
  if (hasMore.value === false) return

  loadingMore.value = true
  currentPage.value += 1
  await loadFavorites(false)
}

// ── Remove Favorite ─────────────────────────────────────────────────────────
function onRemoveFavorite(item: FavoriteItemOut): void {
  uni.showModal({
    title: '取消收藏',
    content: `确定要取消收藏「${item.name}」吗？`,
    confirmText: '确定',
    confirmColor: '#FF7B7B',
    success: async (res) => {
      if (res.confirm) {
        try {
          await removeFavorite(item.product_id)
          favorites.value = favorites.value.filter(
            (f) => f.product_id !== item.product_id
          )
          totalCount.value = Math.max(0, totalCount.value - 1)
          uni.showToast({ title: '已取消收藏', icon: 'success', duration: 1500 })
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
  loadFavorites(true)
})
</script>

<style scoped>
.favorites-page {
  min-height: 100vh;
  background: #FFF8F0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ========================================================================== */
/*  HEADER                                                                     */
/* ========================================================================== */
.favorites-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
}

.favorites-header__count {
  font-size: 24rpx;
  color: #7a6a5a;
}

/* ========================================================================== */
/*  SCROLL AREA                                                                */
/* ========================================================================== */
.favorites-scroll {
  padding: 0 20rpx;
}

.favorites-list-spacer {
  height: 40rpx;
}

/* ========================================================================== */
/*  FAVORITE ITEM CARD                                                         */
/* ========================================================================== */
.favorite-item {
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
.favorite-item__img-wrap {
  width: 160rpx;
  height: 160rpx;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  background: #f5f0eb;
}

.favorite-item__image {
  width: 100%;
  height: 100%;
}

.favorite-item__image-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5ebe0, #faf5f0);
}

.favorite-item__image-emoji {
  font-size: 56rpx;
  line-height: 1;
}

/* Info */
.favorite-item__info {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.favorite-item__name {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 8rpx;
}

.favorite-item__price-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 6rpx;
}

.favorite-item__price {
  font-size: 30rpx;
  font-weight: 600;
  color: #FF7B7B;
}

.favorite-item__time {
  font-size: 22rpx;
  color: #7a6a5a;
  line-height: 1.3;
}

/* Remove Button (heart icon) */
.favorite-item__remove {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.favorite-item__remove-icon {
  font-size: 36rpx;
  color: #FF7B7B;
  line-height: 1;
}

/* ========================================================================== */
/*  LOAD MORE                                                                  */
/* ========================================================================== */
.favorites-load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
}

.favorites-load-more__text {
  font-size: 24rpx;
  color: #7a6a5a;
}

.favorites-load-more__text--done {
  color: #bfb0a0;
}
</style>
