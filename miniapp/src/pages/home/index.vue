<template>
  <view class="page has-custom-tabbar">
    <!-- ① 品牌头图。状态栏高度由头图自己扛（Task 5），页面不用管 -->
    <BrandHero
      title="蓓贝婴童"
      slogan="源头工厂 · 一件代发"
      show-login
      show-search
      @login="onLogin"
      @search="onHeroSearch"
    />

    <!-- ② 上叠白卡：入口 / 分类 / 权益 -->
    <SurfaceCard overlap>
      <EntryGrid :items="ENTRY_ITEMS" @select="onEntrySelect" />

      <!-- 分类没加载出来时整块不渲染：否则两条分隔线夹着一个空行 -->
      <template v-if="categoryEntries.length || sectionErrors.categories">
        <view class="home__divider" />
        <CircleEntryRow
          v-if="categoryEntries.length"
          :items="categoryEntries"
          @select="onCategorySelect"
        />
        <view v-else class="home__section-error" @tap="fetchCategories()">
          <AppIcon name="reload" :size="30" tone="muted" />
          <text class="home__section-error-text">分类加载失败，点击重试</text>
        </view>
      </template>

      <view class="home__divider" />

      <BenefitCard
        :main="BENEFIT_MAIN"
        :side="BENEFIT_SIDE"
        @main-tap="goToMember"
        @side-tap="onBenefitSide"
      />
    </SurfaceCard>

    <!-- 骨架屏放在白卡正下方（而不是所有分区之后）：分区是数据驱动的，
         等 loading 走完再渲染，骨架才不会被顶到首屏以外去。 -->
    <PageLoading v-if="pageState === 'loading'" />

    <EmptyState
      v-else-if="pageState === 'error'"
      title="加载失败"
      description="检查网络后点击重试"
      :show-button="true"
      button-text="重新加载"
      @button-click="retryAll"
    />

    <template v-else>
      <!-- ③ 蓓贝推荐 -->
      <SectionHeader title="蓓贝推荐" more="查看更多" @more="goToMoreProducts" />
      <view
        v-if="sectionErrors.recommend"
        class="home__section-error"
        @tap="fetchRecommendProducts()"
      >
        <AppIcon name="reload" :size="30" tone="muted" />
        <text class="home__section-error-text">推荐商品加载失败，点击重试</text>
      </view>
      <scroll-view v-else class="home__scroll" scroll-x :show-scrollbar="false" enhanced>
        <view class="home__scroll-inner">
          <view v-for="p in recommendProducts" :key="p.id" class="home__scroll-item">
            <ProductCard :product="p" @click="goToProduct" />
          </view>
        </view>
      </scroll-view>

      <!-- ④ 设计案例：横滑横图卡 -->
      <SectionHeader title="设计案例" more="查看更多" @more="goToMoreCases" />
      <view
        v-if="sectionErrors.cases"
        class="home__section-error"
        @tap="fetchCases()"
      >
        <AppIcon name="reload" :size="30" tone="muted" />
        <text class="home__section-error-text">设计案例加载失败，点击重试</text>
      </view>
      <scroll-view v-else class="home__scroll" scroll-x :show-scrollbar="false" enhanced>
        <view class="home__scroll-inner">
          <BannerCard
            v-for="c in caseItems"
            :key="c.id"
            :title="c.title"
            :subtitle="[c.store_area_range, (c.style_tags || [])[0]].filter(Boolean).join(' · ')"
            :image="c.images?.[0]"
            width="520rpx"
            @tap="goToCase(c.id)"
          />
        </view>
      </scroll-view>

      <!-- ⑤ 品牌活动：满宽横图卡 -->
      <SectionHeader title="品牌活动" />
      <view class="home__banners">
        <BannerCard
          v-for="promo in promotions"
          :key="promo.id"
          :title="promo.title"
          :subtitle="promoSubtitle(promo)"
          action="立即参与"
          @tap="onPromotionTap"
        />
      </view>

      <!-- ⑥ 热门商品 2 列瀑布流 -->
      <SectionHeader title="热门商品" />
      <view
        v-if="sectionErrors.hot"
        class="home__section-error"
        @tap="fetchHotProducts(true)"
      >
        <AppIcon name="reload" :size="30" tone="muted" />
        <text class="home__section-error-text">热门商品加载失败，点击重试</text>
      </view>
      <template v-else>
        <view class="home__grid">
          <ProductCard
            v-for="p in hotProducts"
            :key="p.id"
            class="home__grid-item"
            :product="p"
            @click="goToProduct"
          />
        </view>
        <EmptyState
          v-if="!hotLoadingMore && hotProducts.length === 0"
          title="暂无商品"
          description="换个分类看看，或联系客服获取最新货源"
        />
        <view v-if="hotLoadingMore" class="home__loading-more">加载中…</view>
        <view v-if="hotNoMore && hotProducts.length" class="home__loading-more">已经到底了</view>
      </template>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { onLoad, onShow, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import AppIcon from '../../components/AppIcon.vue'
import BrandHero from '../../components/BrandHero.vue'
import SurfaceCard from '../../components/SurfaceCard.vue'
import SectionHeader from '../../components/SectionHeader.vue'
import EntryGrid from '../../components/EntryGrid.vue'
import CircleEntryRow from '../../components/CircleEntryRow.vue'
import BenefitCard from '../../components/BenefitCard.vue'
import BannerCard from '../../components/BannerCard.vue'
import ProductCard from '../../components/ProductCard.vue'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { useAppStore } from '../../stores/app'
import { getCategories, getNewProducts, getProductList } from '../../api/products'
import { getCaseList } from '../../api/cases'
import http from '../../api/request'
import type { Category as CategoryType, ProductListItem } from '../../api/products'
import type { DesignCase } from '../../api/cases'
import { PAGE_SIZE } from '../../utils/constants'
import { applyFallback } from '../../mock/fallback'
import {
  DEMO_CASES,
  DEMO_CATEGORIES,
  DEMO_PRODUCTS,
  DEMO_PROMOTIONS,
} from '../../mock/demo-data'

const appStore = useAppStore()

// ── Init app store ──────────────────────────────────────────────────────────
// 首页是小程序的首屏，状态栏高度得在这里就备好 —— BrandHero 直接读它。
appStore.init()

// ── Page State ──────────────────────────────────────────────────────────────
type PageState = 'loading' | 'error' | 'content'
const pageState = ref<PageState>('loading')

// ── Section-level errors (only meaningful when pageState is 'content') ─────
const sectionErrors = reactive({
  categories: false,
  recommend: false,
  cases: false,
  hot: false,
})

// ── 固定文案（不依赖后端） ──────────────────────────────────────────────
const ENTRY_ITEMS = [
  { icon: 'bag-fill', title: '一件代发', subtitle: '无起批压力' },
  { icon: 'rmb-circle', title: '批量询价', subtitle: '量大更优' },
  { icon: 'photo', title: '定制打样', subtitle: '专属 LOGO' },
]

const BENEFIT_MAIN = {
  title: '会员权益',
  desc: '等级越高折扣越低\n账期最长 60 天',
  action: '查看权益',
}
const BENEFIT_SIDE = [
  { icon: 'integral', title: '积分抽奖', desc: '即将上线' },
  { icon: 'gift', title: '新品首发', desc: '优先订货' },
]

// ── Categories ──────────────────────────────────────────────────────────────
const categories = ref<CategoryType[]>([])

// 后端 Category 的 icon 目前恒为 null，图标按索引轮换一组通用品类图标，
// 比让所有分类共用一个图标更有信息量。
const CATEGORY_ICONS = ['bag', 'coupon', 'home', 'photo', 'integral']

const categoryEntries = computed(() =>
  categories.value.map((c, i) => ({
    id: c.id,
    icon: CATEGORY_ICONS[i % CATEGORY_ICONS.length],
    label: c.name,
  })),
)

async function fetchCategories() {
  sectionErrors.categories = false
  try {
    const res = await getCategories()
    categories.value = applyFallback(res.data, DEMO_CATEGORIES)
  } catch {
    sectionErrors.categories = true
    categories.value = []
  }
}

function onEntrySelect(index: number) {
  uni.showToast({ title: ENTRY_ITEMS[index].title, icon: 'none' })
}

function onCategorySelect(index: number) {
  const cat = categoryEntries.value[index]
  if (!cat) return
  // /pages/products/index 是 tabBar 页，只能用 switchTab；而 switchTab 不支持
  // query 传参，所以把 category_id 写进 storage，由商品页在 onShow 里取。
  uni.setStorageSync('products_pending_category', cat.id)
  uni.switchTab({ url: '/pages/products/index' })
}

function goToMember() {
  uni.navigateTo({ url: '/pages/mine/member/index' })
}

function onBenefitSide(index: number) {
  uni.showToast({
    title: index === 0 ? '积分抽奖即将上线' : '新品首发敬请期待',
    icon: 'none',
  })
}

// /pages/mine/index 同样是 tabBar 页
function onLogin() {
  uni.switchTab({ url: '/pages/mine/index' })
}

// 头图的搜索框带回关键词。同样只能 storage + switchTab。
function onHeroSearch(kw: string) {
  if (kw.trim()) uni.setStorageSync('products_pending_keyword', kw.trim())
  uni.switchTab({ url: '/pages/products/index' })
}

// ── 蓓贝推荐（横滑） ────────────────────────────────────────────────────
const recommendProducts = ref<ProductListItem[]>([])

async function fetchRecommendProducts() {
  sectionErrors.recommend = false
  try {
    const res = await getNewProducts(10)
    // 空集合兜底；请求失败走 catch，保持空 -> 该分区显示重试，但不盖假数据
    recommendProducts.value = applyFallback(res.data, DEMO_PRODUCTS)
  } catch {
    sectionErrors.recommend = true
    recommendProducts.value = []
  }
}

// ── 设计案例（横滑横图卡） ──────────────────────────────────────────────
const caseItems = ref<DesignCase[]>([])

async function fetchCases() {
  sectionErrors.cases = false
  try {
    const res = await getCaseList({ page: 1, page_size: 4 })
    // 分页形状是 items，不是 list —— 后端 PaginatedResponse 就是 items/total。
    caseItems.value = applyFallback(res.data.items, DEMO_CASES)
  } catch {
    sectionErrors.cases = true
    caseItems.value = []
  }
}

// ── 品牌活动 ────────────────────────────────────────────────────────────
const promotions = ref<typeof DEMO_PROMOTIONS>([])

async function fetchPromotions() {
  try {
    const res: any = await http.get('/promotions/active')
    promotions.value = applyFallback(res.data, DEMO_PROMOTIONS)
  } catch {
    promotions.value = []
  }
}

/** rules 里的金额单位是分（见后端 models/promotion.py 的注释） */
function promoSubtitle(promo: { type: string; rules: any }): string {
  const r = promo.rules || {}
  if (promo.type === 'full_reduction') {
    return `满 ${Math.round(r.threshold / 100)} 减 ${Math.round(r.reduce / 100)}`
  }
  if (promo.type === 'discount') return `${(r.rate * 10).toFixed(1)} 折`
  if (promo.type === 'flash_sale') return `限时价 ¥${(r.price / 100).toFixed(0)}`
  return ''
}

function onPromotionTap() {
  goToMoreProducts()
}

// ── 热门商品（2 列 + 触底加载） ─────────────────────────────────────────
const hotProducts = ref<ProductListItem[]>([])
const hotPage = ref(1)
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
      sort: 'sales_desc',
    })
    const { items, total } = res.data
    if (reset) {
      hotProducts.value = applyFallback(items, DEMO_PRODUCTS)
    } else {
      hotProducts.value.push(...(items || []))
    }
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
      fetchCategories(),
      fetchRecommendProducts(),
      fetchCases(),
      fetchPromotions(),
      fetchHotProducts(true),
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
// 自定义 tabBar 是每个页面各自渲染的一份实例，状态不共享。这里写下本页在
// tabs 数组里的下标（首页 = 0）。组件优先按页面栈推断选中项，存储是回落值。
onShow(() => {
  uni.setStorageSync('tabbar_selected', 0)
})

onLoad(() => {
  loadAllData()
})

onPullDownRefresh(() => {
  Promise.all([
    fetchCategories(),
    fetchRecommendProducts(),
    fetchCases(),
    fetchPromotions(),
    fetchHotProducts(true),
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

// 这两个目标都是 tabBar 页，navigateTo 跳不过去（点了没反应），必须 switchTab。
function goToMoreProducts() {
  uni.switchTab({ url: '/pages/products/index' })
}

function goToMoreCases() {
  uni.switchTab({ url: '/pages/cases/index' })
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-primary);
}

.home__divider {
  height: 1rpx;
  background: var(--border-light);
  margin: var(--space-lg) 0;
}

/* 横滑容器：内层 inline-flex + 首尾 padding，让卡片能滑出屏幕边缘，
   从而在静止时就露出下一张的一角 —— 「还有更多」的天然提示。 */
.home__scroll {
  width: 100%;
  white-space: nowrap;
}

.home__scroll-inner {
  display: inline-flex;
  gap: var(--space-md);
  padding: 0 var(--space-lg);
}

.home__scroll-item {
  width: 260rpx;
  flex-shrink: 0;
}

.home__banners {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: 0 var(--space-lg);
}

.home__grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  padding: 0 var(--space-lg);
}

.home__grid-item {
  width: calc((100% - var(--space-md)) / 2);
}

.home__section-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: var(--space-xl);
  color: var(--text-muted);
}

.home__section-error-text {
  font-size: var(--font-sm);
}

.home__loading-more {
  text-align: center;
  padding: var(--space-lg);
  font-size: var(--font-sm);
  color: var(--text-muted);
}
</style>
