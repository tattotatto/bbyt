<template>
  <view class="home-page">
    <!-- ================================================================ -->
    <!--  STATE: LOADING -->
    <!-- ================================================================ -->
    <template v-if="pageState === 'loading'">
      <view class="home-nav home-nav--loading" :style="{ paddingTop: statusBarHeight + 'px' }">
        <view class="home-nav__inner">
          <text class="home-nav__brand-icon">🧸</text>
          <text class="home-nav__title">HX Mall</text>
          <view style="width:120rpx" />
        </view>
      </view>
      <PageLoading type="card" :count="4" />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: ERROR (full page) -->
    <!-- ================================================================ -->
    <template v-else-if="pageState === 'error'">
      <EmptyState
        icon="⚠️"
        title="加载失败"
        description="网络好像开小差了，请检查网络后重试"
        :showButton="true"
        buttonText="重新加载"
        @buttonClick="retryAll"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: CONTENT -->
    <!-- ================================================================ -->
    <template v-else>
      <!-- 1. Custom Navigation Bar -->
      <view class="home-nav" :style="{ paddingTop: statusBarHeight + 'px' }">
        <view class="home-nav__inner">
          <view class="home-nav__left">
            <text class="home-nav__brand-icon">🧸</text>
          </view>
          <text class="home-nav__title">HX Mall</text>
          <view class="home-nav__right">
            <view class="home-nav__icon" @tap="goToSearch">
              <text class="home-nav__icon-text">🔍</text>
            </view>
            <view class="home-nav__icon home-nav__cart" @tap="onCartTap">
              <text class="home-nav__icon-text">🛒</text>
              <text v-if="cartStore.totalCount > 0" class="home-nav__badge">
                {{ cartStore.totalCount > 99 ? '99+' : cartStore.totalCount }}
              </text>
            </view>
          </view>
        </view>
      </view>

      <!-- 2. Search Bar -->
      <view class="home-search">
        <SearchBar
          v-model="searchKeyword"
          placeholder="搜索儿童产品..."
          @search="onSearch"
        />
      </view>

      <!-- 3. Banner Carousel -->
      <view v-if="banners.length > 0" class="home-banners">
        <swiper
          class="home-banners__swiper"
          :indicator-dots="true"
          :autoplay="true"
          :interval="4000"
          :duration="500"
          :circular="true"
          indicator-color="rgba(255,255,255,0.5)"
          indicator-active-color="#FF7B7B"
        >
          <swiper-item v-for="(banner, index) in banners" :key="index">
            <view
              class="home-banner"
              :style="{ background: banner.gradient }"
            >
              <view class="home-banner__content">
                <text class="home-banner__emoji">{{ banner.emoji }}</text>
                <text class="home-banner__title">{{ banner.title }}</text>
                <text class="home-banner__desc">{{ banner.desc }}</text>
              </view>
            </view>
          </swiper-item>
        </swiper>
      </view>

      <!-- 4. Category Quick Nav -->
      <view v-if="categories.length > 0" class="home-categories">
        <view
          v-for="(cat, idx) in categories"
          :key="cat.id"
          class="home-category"
          @tap="goToCategory(cat)"
        >
          <view
            class="home-category__icon"
            :style="{ background: categoryBgColor(idx) }"
          >
            <text class="home-category__emoji">{{ cat.icon || '📦' }}</text>
          </view>
          <text class="home-category__label">{{ cat.name }}</text>
        </view>
      </view>
      <!-- Category error -->
      <view v-else-if="sectionErrors.categories" class="home-section-error">
        <text class="home-section-error__text">分类加载失败</text>
        <text class="home-section-error__retry" @tap="fetchCategories">点击重试</text>
      </view>

      <!-- 5. 「小暖推荐」Section — Horizontal Scroll -->
      <view v-if="recommendProducts.length > 0" class="home-section">
        <view class="home-section__header">
          <view class="home-section__left">
            <view class="home-section__bar" />
            <text class="home-section__title">小暖推荐</text>
          </view>
          <text class="home-section__more" @tap="goToMoreProducts">查看更多 ›</text>
        </view>
        <scroll-view
          class="home-recommend-scroll"
          :scroll-x="true"
          :show-scrollbar="false"
        >
          <view class="home-recommend-list">
            <ProductCard
              v-for="product in recommendProducts"
              :key="product.id"
              :product="product"
              class="home-recommend-card"
              @click="goToProduct"
            />
          </view>
        </scroll-view>
      </view>
      <!-- Recommend error -->
      <view v-else-if="sectionErrors.recommend" class="home-section-error">
        <text class="home-section-error__text">推荐商品加载失败</text>
        <text class="home-section-error__retry" @tap="fetchRecommendProducts">点击重试</text>
      </view>

      <!-- 6. 「设计案例」Section — 2-col Waterfall -->
      <view v-if="caseItems.length > 0" class="home-section">
        <view class="home-section__header">
          <view class="home-section__left">
            <view class="home-section__bar" />
            <text class="home-section__title">设计案例</text>
          </view>
          <text class="home-section__more" @tap="goToMoreCases">查看更多 ›</text>
        </view>
        <view class="home-cases-grid">
          <CaseCard
            v-for="caseItem in caseItems"
            :key="caseItem.id"
            :caseData="caseItem"
            class="home-case-card"
            @click="goToCase"
          />
        </view>
      </view>
      <!-- Cases error -->
      <view v-else-if="sectionErrors.cases" class="home-section-error">
        <text class="home-section-error__text">设计案例加载失败</text>
        <text class="home-section-error__retry" @tap="fetchCases">点击重试</text>
      </view>

      <!-- 7. 「热门商品」Section — 2-col Grid with Load More -->
      <view v-if="hotProducts.length > 0" class="home-section">
        <view class="home-section__header">
          <view class="home-section__left">
            <view class="home-section__bar" />
            <text class="home-section__title">热门商品</text>
          </view>
        </view>
        <view class="home-hot-grid">
          <ProductCard
            v-for="product in hotProducts"
            :key="product.id"
            :product="product"
            class="home-hot-card"
            @click="goToProduct"
          />
        </view>
        <!-- Load more states -->
        <view v-if="hotLoadingMore" class="home-load-more">
          <text class="home-load-more__text">加载中...</text>
        </view>
        <view v-else-if="hotNoMore" class="home-load-more">
          <text class="home-load-more__text home-load-more__text--muted">— 已经到底了 —</text>
        </view>
      </view>
      <!-- Hot products error -->
      <view v-else-if="sectionErrors.hot" class="home-section-error">
        <text class="home-section-error__text">热门商品加载失败</text>
        <text class="home-section-error__retry" @tap="fetchHotProducts">点击重试</text>
      </view>

      <!-- Bottom Safe Area -->
      <view class="home-safe-bottom" :style="{ height: safeBottom + 'px' }" />
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import SearchBar from '../../components/SearchBar.vue'
import ProductCard from '../../components/ProductCard.vue'
import CaseCard from '../../components/CaseCard.vue'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { useCartStore } from '../../stores/cart'
import { useAppStore } from '../../stores/app'
import {
  getCategories,
  getHotProducts,
  getNewProducts,
  getProductList
} from '../../api/products'
import { getCaseList } from '../../api/cases'
import type { Product, Category as CategoryType } from '../../api/products'
import type { DesignCase } from '../../api/cases'
import { PAGE_SIZE } from '../../utils/constants'

const cartStore = useCartStore()
const appStore = useAppStore()

// ── Init app store ──────────────────────────────────────────────────────────
appStore.init()

const statusBarHeight = computed(() => appStore.statusBarHeight)
const safeBottom = computed(() => Math.max(appStore.safeAreaBottom, 20))

// ── Page State ──────────────────────────────────────────────────────────────
type PageState = 'loading' | 'error' | 'content'
const pageState = ref<PageState>('loading')

// ── Section-level errors (only meaningful when pageState is 'content') ─────
const sectionErrors = reactive({
  categories: false,
  recommend: false,
  cases: false,
  hot: false
})

// ── Search ──────────────────────────────────────────────────────────────────
const searchKeyword = ref('')

function onSearch(keyword: string) {
  uni.navigateTo({
    url: `/pages/products/index?keyword=${encodeURIComponent(keyword)}`
  })
}

function goToSearch() {
  uni.navigateTo({ url: '/pages/products/index?focus=1' })
}

function onCartTap() {
  uni.showToast({ title: '购物车功能开发中', icon: 'none' })
}

// ── Banners ─────────────────────────────────────────────────────────────────
const BANNER_GRADIENTS = [
  'linear-gradient(135deg, #FF7B7B 0%, #FFB3B3 100%)',
  'linear-gradient(135deg, #7EC8E3 0%, #A8DFF0 100%)',
  'linear-gradient(135deg, #A8D8B9 0%, #C8E8D4 100%)',
  'linear-gradient(135deg, #FFB347 0%, #FFCC80 100%)',
  'linear-gradient(135deg, #B8A8D8 0%, #D4C8E8 100%)'
]
const BANNER_EMOJIS = ['🎁', '⚡', '🎨', '🌟', '💎']

interface Banner {
  gradient: string
  emoji: string
  title: string
  desc: string
}

const banners = ref<Banner[]>([])

async function fetchBanners() {
  try {
    const res = await getHotProducts(5)
    const products = res.data || []
    banners.value = products.slice(0, 5).map((p, i) => ({
      gradient: BANNER_GRADIENTS[i % BANNER_GRADIENTS.length],
      emoji: BANNER_EMOJIS[i % BANNER_EMOJIS.length],
      title: p.name,
      desc: `${p.age_range || p.name || ''} · 爆款热销`
    }))
  } catch {
    // Banner failure is non-critical; use fallback
    banners.value = [
      { gradient: BANNER_GRADIENTS[0], emoji: '🎁', title: '新品上架', desc: '探索最新儿童好物' },
      { gradient: BANNER_GRADIENTS[1], emoji: '⚡', title: '限时特惠', desc: '精选好物限时折扣' },
      { gradient: BANNER_GRADIENTS[2], emoji: '🎨', title: '设计灵感', desc: '打造温馨亲子空间' }
    ]
  }
}

// ── Categories ──────────────────────────────────────────────────────────────
const CATEGORY_BG_COLORS = ['#FFF0F0', '#F0F8FB', '#F2FAF5', '#FFFBE6']

const categories = ref<CategoryType[]>([])

function categoryBgColor(index: number): string {
  return CATEGORY_BG_COLORS[index % CATEGORY_BG_COLORS.length]
}

async function fetchCategories() {
  sectionErrors.categories = false
  try {
    const res = await getCategories()
    categories.value = res.data || []
  } catch {
    sectionErrors.categories = true
    categories.value = []
  }
}

function goToCategory(cat: CategoryType) {
  uni.navigateTo({
    url: `/pages/products/index?category_id=${cat.id}`
  })
}

// ── Recommend Products (Horizontal Scroll) ──────────────────────────────────
const recommendProducts = ref<Product[]>([])

async function fetchRecommendProducts() {
  sectionErrors.recommend = false
  try {
    const res = await getNewProducts(10)
    recommendProducts.value = res.data || []
  } catch {
    sectionErrors.recommend = true
    recommendProducts.value = []
  }
}

// ── Design Cases (2-col Waterfall) ──────────────────────────────────────────
const caseItems = ref<DesignCase[]>([])

async function fetchCases() {
  sectionErrors.cases = false
  try {
    const res = await getCaseList({ page: 1, page_size: 4 })
    caseItems.value = res.data.list || []
  } catch {
    sectionErrors.cases = true
    caseItems.value = []
  }
}

// ── Hot Products (2-col Grid + Pagination) ──────────────────────────────────
const hotProducts = ref<Product[]>([])
const hotPage = ref(1)
const hotTotal = ref(0)
const hotLoadingMore = ref(false)
const hotNoMore = ref(false)

async function fetchHotProducts(reset = true) {
  if (reset) {
    hotPage.value = 1
    hotNoMore.value = false
    sectionErrors.hot = false
  }

  if (hotLoadingMore.value) return

  hotLoadingMore.value = true
  try {
    const res = await getProductList({
      page: hotPage.value,
      page_size: PAGE_SIZE,
      sort: 'sales_desc'
    })
    const { items, total } = res.data
    if (reset) {
      hotProducts.value = items || []
    } else {
      hotProducts.value.push(...(items || []))
    }
    hotTotal.value = total
    hotNoMore.value = hotProducts.value.length >= total
  } catch {
    if (reset) {
      sectionErrors.hot = true
      hotProducts.value = []
    }
    uni.showToast({ title: '加载失败，请重试', icon: 'none' })
  } finally {
    hotLoadingMore.value = false
  }
}

async function loadMoreHot() {
  if (hotNoMore.value || hotLoadingMore.value) return
  hotPage.value++
  await fetchHotProducts(false)
}

// ── Aggregate Load ──────────────────────────────────────────────────────────
async function loadAllData() {
  pageState.value = 'loading'
  try {
    await Promise.all([
      fetchBanners(),
      fetchCategories(),
      fetchRecommendProducts(),
      fetchCases(),
      fetchHotProducts(true)
    ])
    pageState.value = 'content'
  } catch {
    pageState.value = 'error'
  }
}

async function retryAll() {
  await loadAllData()
}

// ── Lifecycle ───────────────────────────────────────────────────────────────
onLoad(() => {
  loadAllData()
})

onPullDownRefresh(() => {
  Promise.all([
    fetchBanners(),
    fetchCategories(),
    fetchRecommendProducts(),
    fetchCases(),
    fetchHotProducts(true)
  ]).finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  loadMoreHot()
})

// ── Navigation ──────────────────────────────────────────────────────────────
function goToProduct(id: string | number) {
  uni.navigateTo({ url: `/pages/products/detail?id=${id}` })
}

function goToCase(id: string | number) {
  uni.navigateTo({ url: `/pages/cases/detail?id=${id}` })
}

function goToMoreProducts() {
  uni.navigateTo({ url: '/pages/products/index' })
}

function goToMoreCases() {
  uni.navigateTo({ url: '/pages/cases/index' })
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #FFF8F0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ========================================================================== */
/*  CUSTOM NAVIGATION BAR                                                     */
/* ========================================================================== */
.home-nav {
  background: #FF7B7B;
  position: sticky;
  top: 0;
  z-index: 100;
}

.home-nav--loading {
  position: relative;
}

.home-nav__inner {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 20rpx;
}

.home-nav__left {
  width: 80rpx;
  display: flex;
  align-items: center;
}

.home-nav__brand-icon {
  font-size: 32rpx;
  line-height: 1;
}

.home-nav__title {
  font-size: 34rpx;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 4rpx;
}

.home-nav__right {
  width: 120rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-end;
  gap: 16rpx;
}

.home-nav__icon {
  position: relative;
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.home-nav__icon-text {
  font-size: 36rpx;
  line-height: 1;
}

.home-nav__badge {
  position: absolute;
  top: -4rpx;
  right: -8rpx;
  min-width: 32rpx;
  height: 32rpx;
  line-height: 32rpx;
  font-size: 20rpx;
  font-weight: 600;
  color: #ffffff;
  background: #FFD93D;
  border-radius: 50px;
  text-align: center;
  padding: 0 6rpx;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

/* ========================================================================== */
/*  SEARCH BAR                                                                */
/* ========================================================================== */
.home-search {
  padding: 20rpx 24rpx;
  background: #FF7B7B;
}

/* ========================================================================== */
/*  BANNER CAROUSEL                                                           */
/* ========================================================================== */
.home-banners {
  padding: 0 20rpx;
  margin-top: 20rpx;
}

.home-banners__swiper {
  width: 100%;
  height: 400rpx;
  border-radius: 20px;
  overflow: hidden;
}

.home-banner {
  width: 100%;
  height: 400rpx;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30rpx;
}

.home-banner__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.home-banner__emoji {
  font-size: 72rpx;
  line-height: 1;
  margin-bottom: 12rpx;
}

.home-banner__title {
  font-size: 40rpx;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0 20rpx;
}

.home-banner__desc {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
}

/* ========================================================================== */
/*  CATEGORY GRID                                                             */
/* ========================================================================== */
.home-categories {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  padding: 24rpx 8rpx 10rpx;
  background: #ffffff;
  margin: 20rpx 20rpx;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.home-category {
  width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 0;
}

.home-category__icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10rpx;
}

.home-category__emoji {
  font-size: 40rpx;
  line-height: 1;
}

.home-category__label {
  font-size: 22rpx;
  color: #4a3728;
  text-align: center;
  line-height: 1.3;
}

/* ========================================================================== */
/*  SECTION HEADER                                                            */
/* ========================================================================== */
.home-section {
  padding: 0 20rpx;
  margin-top: 32rpx;
}

.home-section__header {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.home-section__left {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.home-section__bar {
  width: 4px;
  height: 32rpx;
  border-radius: 2px;
  background: #FF7B7B;
  margin-right: 16rpx;
}

.home-section__title {
  font-size: 32rpx;
  font-weight: 600;
  color: #4a3728;
}

.home-section__more {
  font-size: 26rpx;
  color: #7a6a5a;
  padding: 4rpx 0;
}

/* ========================================================================== */
/*  SECTION ERROR (inline)                                                    */
/* ========================================================================== */
.home-section-error {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  padding: 32rpx 20rpx;
  gap: 16rpx;
}

.home-section-error__text {
  font-size: 26rpx;
  color: #b0a090;
}

.home-section-error__retry {
  font-size: 26rpx;
  color: #FF7B7B;
  font-weight: 500;
}

/* ========================================================================== */
/*  RECOMMEND PRODUCTS — Horizontal Scroll                                    */
/* ========================================================================== */
.home-recommend-scroll {
  white-space: nowrap;
}

.home-recommend-list {
  display: flex;
  flex-direction: row;
  gap: 20rpx;
  padding-bottom: 8rpx;
}

.home-recommend-card {
  width: 280rpx;
  flex-shrink: 0;
}

/* ========================================================================== */
/*  DESIGN CASES — 2-col Waterfall Grid                                       */
/* ========================================================================== */
.home-cases-grid {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 20rpx;
}

.home-case-card {
  width: calc(50% - 10rpx);
}

/* ========================================================================== */
/*  HOT PRODUCTS — 2-col Grid                                                 */
/* ========================================================================== */
.home-hot-grid {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 20rpx;
}

.home-hot-card {
  width: calc(50% - 10rpx);
}

/* ========================================================================== */
/*  LOAD MORE                                                                 */
/* ========================================================================== */
.home-load-more {
  display: flex;
  justify-content: center;
  padding: 32rpx 0;
}

.home-load-more__text {
  font-size: 26rpx;
  color: #7a6a5a;
}

.home-load-more__text--muted {
  color: #b0a090;
}

/* ========================================================================== */
/*  BOTTOM SAFE AREA                                                          */
/* ========================================================================== */
.home-safe-bottom {
  width: 100%;
}
</style>
