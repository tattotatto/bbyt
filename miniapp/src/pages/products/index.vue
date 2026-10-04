<template>
  <view class="page has-custom-tabbar">
    <!-- ① 品牌头图，紧凑版 + 搜索框 -->
    <BrandHero
      title="商品"
      :compact="true"
      show-search
      @search="onSearchConfirm"
    />

    <!-- ② 上叠白卡：分类横滚。
         选中态是「品牌色文字 + 下划短线」而不是实心胶囊 —— 圆形入口那套
         在首页已经用过，这里再用一次会显得单调；而且文字 tab 条能容纳的
         分类数量更多，横滑时也更容易看出还有多少个。 -->
    <SurfaceCard overlap padding="0">
      <scroll-view class="cat" scroll-x :show-scrollbar="false" enhanced>
        <view class="cat__inner">
          <view
            v-for="c in categoryTabs"
            :key="c.id ?? 'all'"
            class="cat__item"
            @tap="onCategorySelect(c.id)"
          >
            <text class="cat__label" :class="{ 'cat__label--active': activeCategoryId === c.id }">
              {{ c.name }}
            </text>
            <view v-if="activeCategoryId === c.id" class="cat__underline" />
          </view>
        </view>
      </scroll-view>
    </SurfaceCard>

    <!-- ③ 排序条。「价格」这一格带箭头，重复点它是升降序切换 -->
    <view class="sort">
      <view
        v-for="s in SORTS"
        :key="s.key"
        class="sort__item"
        @tap="onSortSelect(s.key)"
      >
        <text class="sort__label" :class="{ 'sort__label--active': sort === s.key }">
          {{ s.label }}
        </text>
        <AppIcon
          v-if="s.key === 'price'"
          name="arrow-downward"
          :size="24"
          :tone="sort === s.key ? 'primary' : 'muted'"
          :class="{ 'sort__arrow--asc': priceAsc }"
        />
        <AppIcon
          v-else-if="s.key === 'filter'"
          name="arrow-downward"
          :size="24"
          :tone="showFilter || filterActive ? 'primary' : 'muted'"
          :class="{ 'sort__arrow--asc': showFilter }"
        />
      </view>
    </view>

    <!-- 筛选行：「筛选」那一格展开的二级面板。适龄档位取自 utils/constants，
         不在这里另抄一份 —— 抄错一个字后端是精确匹配（age_range == 传入值），
         筛出来直接是空的，而且不报错。 -->
    <view v-if="showFilter" class="filter">
      <view class="filter__group">
        <view
          v-for="(a, i) in AGE_TABS"
          :key="a.label"
          class="chip"
          :class="{ 'chip--active': ageIndex === i }"
          @tap="onAgeSelect(i)"
        >
          <text class="chip__text">{{ a.label }}</text>
        </view>
        <view
          class="chip"
          :class="{ 'chip--active': onlyInStock }"
          @tap="toggleStockFilter"
        >
          <text class="chip__text">仅看有货</text>
        </view>
      </view>
    </view>

    <!-- 骨架屏紧贴筛选区下方而不是排在网格之后：等状态互斥地渲染，
         否则 loading 时上面那片空网格已经把骨架顶出首屏了。 -->
    <PageLoading v-if="loading" />

    <EmptyState
      v-else-if="errorMsg"
      :title="errorMsg"
      description="检查网络后点击重试"
      :show-button="true"
      button-text="重新加载"
      @button-click="retry"
    />

    <template v-else>
      <!-- ④ 两列瀑布流 -->
      <view class="grid">
        <ProductCard
          v-for="p in products"
          :key="p.id"
          class="grid__item"
          :product="p"
          @click="goToDetail"
        />
      </view>

      <EmptyState
        v-if="products.length === 0 && !loadingMore"
        title="没有找到商品"
        description="换个分类或关键词试试"
      />

      <view v-if="loadingMore" class="list-foot">加载中…</view>
      <view v-else-if="!hasMore && products.length" class="list-foot">已经到底了</view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad, onShow, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import AppIcon from '../../components/AppIcon.vue'
import BrandHero from '../../components/BrandHero.vue'
import SurfaceCard from '../../components/SurfaceCard.vue'
import ProductCard from '../../components/ProductCard.vue'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { getCategories, getProductList } from '../../api/products'
import type { ProductListItem, ProductListParams, Category } from '../../api/products'
import { AGE_RANGES, PAGE_SIZE } from '../../utils/constants'
import { mergeProductPage } from '../../utils/product-list'

// ── State ──────────────────────────────────────────────
const loading = ref(true)
const errorMsg = ref('')
const products = ref<ProductListItem[]>([])
const page = ref(1)
const loadingMore = ref(false)
const hasMore = ref(true)

// ── Filters ────────────────────────────────────────────
const keyword = ref('')
// Category.id 是后端给的字符串（api/types.ts），不是数字 —— 旧代码这里写的是
// number 并且到处 Number() 一次，属于把契约抹平成了碰巧能用的样子。
const activeCategoryId = ref<string | undefined>(undefined)
const categories = ref<Category[]>([])

const ageIndex = ref(0) // 0 = 全部
const onlyInStock = ref(false)
const showFilter = ref(false)

/** 「筛选」那一格要不要高亮：展开着，或任何一项筛选非默认 */
const filterActive = computed(() => ageIndex.value > 0 || onlyInStock.value)

// ── Sort ───────────────────────────────────────────────
type SortKey = 'default' | 'sales_desc' | 'price' | 'newest'

const SORTS: { key: SortKey | 'filter'; label: string }[] = [
  { key: 'default', label: '综合' },
  { key: 'sales_desc', label: '销量' },
  { key: 'price', label: '价格' },
  { key: 'filter', label: '筛选' },
]

const sort = ref<SortKey>('default')
/** 「价格」这一格的当前方向。单独存一份，因为 price_asc / price_desc
 *  是同一个按钮的两种状态，没法靠 sort === 'price_desc' 判断出来。 */
const priceAsc = ref(false)

/** 送给后端的 sort 参数（'default' 不发，走后端默认排序） */
const sortParam = computed<'newest' | 'sales_desc' | 'price_asc' | 'price_desc' | undefined>(() => {
  if (sort.value === 'default') return undefined
  if (sort.value === 'price') return priceAsc.value ? 'price_asc' : 'price_desc'
  return sort.value
})

function onSortSelect(key: SortKey | 'filter') {
  if (key === 'filter') {
    showFilter.value = !showFilter.value
    return
  }
  if (key === 'price' && sort.value === 'price') {
    // 重复点「价格」：在升降序之间切换，箭头跟着翻
    priceAsc.value = !priceAsc.value
  } else {
    sort.value = key
    if (key === 'price') priceAsc.value = false // 首次进入按价格降序
  }
  loadProducts(true)
}

// ── Categories ─────────────────────────────────────────
const categoryTabs = computed<{ id: string | undefined; name: string }[]>(() => [
  { id: undefined, name: '全部' },
  ...categories.value.map((c) => ({ id: c.id, name: c.name })),
])

async function loadCategories() {
  try {
    const res = await getCategories()
    categories.value = res.data || []
  } catch {
    // 拉不到分类就只剩「全部」，不阻断商品列表
    categories.value = []
  }
}

function onCategorySelect(id: string | undefined) {
  if (activeCategoryId.value === id) return
  activeCategoryId.value = id
  loadProducts(true)
}

// ── Age / stock ────────────────────────────────────────
const AGE_TABS = [{ label: '全部' }, ...AGE_RANGES.map((a) => ({ label: a.label }))]

function onAgeSelect(index: number) {
  ageIndex.value = index
  loadProducts(true)
}

function toggleStockFilter() {
  onlyInStock.value = !onlyInStock.value
  loadProducts(true)
}

// ── Search ─────────────────────────────────────────────
// BrandHero 的 search 只在输入框 confirm 时触发，输入过程中不触发 ——
// 否则每敲一个字打一次接口。
function onSearchConfirm(kw: string) {
  keyword.value = kw
  loadProducts(true)
}

// ── Load products ──────────────────────────────────────
async function loadProducts(isRefresh = false) {
  if (isRefresh) {
    page.value = 1
    loading.value = true
  } else if (page.value === 1) {
    loading.value = true
  } else {
    loadingMore.value = true
  }
  errorMsg.value = ''

  try {
    const params: ProductListParams = { page: page.value, page_size: PAGE_SIZE }
    if (activeCategoryId.value) params.category_id = activeCategoryId.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (ageIndex.value > 0) params.age_range = AGE_RANGES[ageIndex.value - 1].value
    if (sortParam.value) params.sort = sortParam.value

    const res = await getProductList(params)

    // 合并 + 分页判定交给纯函数。原本这两件事写在这里，其中 hasMore 用的是
    // **客户端过滤后**的条数：第 1 页 20 条里只要有 1 条缺货，过滤后 19 < 20
    // 就判定「已经到底了」，后面几页里那些有货的商品再也翻不出来。
    // 提成纯函数是为了让 utils/__tests__/product-list.test.ts 能钉死它。
    const merged = mergeProductPage(res.data.items, products.value, {
      page: page.value,
      pageSize: PAGE_SIZE,
      isRefresh,
      onlyInStock: onlyInStock.value,
    })
    products.value = merged.items
    hasMore.value = merged.hasMore
  } catch (err: any) {
    errorMsg.value = err.message || err.msg || '加载失败'
    if (page.value > 1) page.value--
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function retry() {
  loadProducts(true)
}

function goToDetail(id: string | number) {
  uni.navigateTo({ url: `/pages/products/detail?id=${id}` })
}

// ── Lifecycle ──────────────────────────────────────────
// 自定义 tabBar 是每个页面各自渲染的一份实例，状态不共享。这里写下本页在
// tabs 数组里的下标（商品 = 3，客服占 2）。组件优先按页面栈推断选中项。
onShow(() => {
  uni.setStorageSync('tabbar_selected', 3)

  // 首页的分类横滚和搜索框用 storage 传参：switchTab 会静默丢掉 url 上的
  // query，navigateTo 又跳不到 tabBar 页，只剩这一条路。
  //
  // 必须写在 onShow 而不是 onLoad：从 tabBar 切回来时页面还在页面栈上，
  // onLoad 不会再触发。而读完必须立刻删，否则用户之后每次切回商品页都会被
  // 同一个条件再筛一遍，且没有任何办法把它去掉。
  const pendingCat = uni.getStorageSync('products_pending_category')
  const pendingKw = uni.getStorageSync('products_pending_keyword')

  if (pendingCat || pendingKw) {
    if (pendingCat) {
      uni.removeStorageSync('products_pending_category')
      activeCategoryId.value = pendingCat
    }
    if (pendingKw) {
      uni.removeStorageSync('products_pending_keyword')
      keyword.value = pendingKw
    }
    loadProducts(true)
  }
})

onLoad(() => {
  loadCategories()

  // 冷启动时 onShow 紧随 onLoad —— 如果这次进来带着首页交接的筛选条件，
  // 就让 onShow 去发这一次请求。否则两边各发一次：一个不带 category_id、
  // 一个带，两个请求同时在飞，**后返回的那个决定列表**。带条件的先回来的话，
  // 最终渲染的是未筛选的列表 —— 正好是这轮要修掉的那类静默失效。
  const hasHandoff = !!(
    uni.getStorageSync('products_pending_category') ||
    uni.getStorageSync('products_pending_keyword')
  )
  if (!hasHandoff) loadProducts(true)
})

onPullDownRefresh(() => {
  loadProducts(true).finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  if (!loadingMore.value && hasMore.value) {
    page.value++
    loadProducts()
  }
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-primary);
}

/* ── 分类横滚 ─────────────────────────────────────────── */
.cat {
  width: 100%;
  white-space: nowrap;
}

/* 内层 inline-flex + 首尾 padding，让最后一个分类能滑出屏幕边缘 ——
   静止时就露出半截，是「还能往右滑」的天然提示（同首页横滑区）。 */
.cat__inner {
  display: inline-flex;
  gap: var(--space-xl);
  padding: var(--space-lg);
}

.cat__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.cat__label {
  font-size: var(--font-base);
  color: var(--text-secondary);
}

.cat__label--active {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.cat__underline {
  width: 32rpx;
  height: 4rpx;
  border-radius: 2rpx;
  background: var(--color-primary);
  margin-top: var(--space-xs);
}

/* ── 排序条 ───────────────────────────────────────────── */
.sort {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: var(--space-lg);
  background: var(--bg-white);
}

.sort__item {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
}

.sort__label {
  font-size: var(--font-base);
  color: var(--text-secondary);
}

.sort__label--active {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.sort__arrow--asc {
  transform: rotate(180deg);
}

/* ── 筛选行 ───────────────────────────────────────────── */
.filter {
  background: var(--bg-white);
  padding: 0 var(--space-lg) var(--space-lg);
}

.filter__group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.chip {
  padding: var(--space-2xs) var(--space-base);
  border-radius: var(--radius-pill);
  background: var(--bg-primary);
  border: 1rpx solid var(--border-light);
}

.chip--active {
  background: var(--color-primary-bg);
  border-color: var(--color-primary);
}

.chip__text {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.chip--active .chip__text {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

/* ── 商品网格 ─────────────────────────────────────────── */
.grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  padding: var(--space-lg);
}

.grid__item {
  width: calc((100% - var(--space-md)) / 2);
}

.list-foot {
  text-align: center;
  padding: var(--space-lg);
  font-size: var(--font-sm);
  color: var(--text-muted);
}
</style>
